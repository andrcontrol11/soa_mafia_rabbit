import threading
from random import shuffle
import grpc
from concurrent import futures
import logging
import queue
from collections import defaultdict
from protos import mafia_pb2
from protos import mafia_pb2_grpc


class Session:
    def __init__(self):
        self.roles = ["мафия", "комиссар", "мирный житель", "мирный житель"]
        self.notifications = {}
        self.players_list = list()
        self.cv = threading.Condition()
        self.ready_cnt = 0
        self.votes = defaultdict(int)
        self.players_roles = dict()
        self.last_killed = None
        self.last_checked = None
        self.barrier = threading.Barrier(4)


class SoaMafiaServer(mafia_pb2_grpc.SoaMafiaServerServicer):
    def __init__(self):
        self.sessions = defaultdict(Session)

    def RegistratePlayer(self, request, context):
        self.sessions[request.room_name].players_list.append(request.name)
        for notification in self.sessions[request.room_name].notifications:
            self.sessions[request.room_name].notifications[notification].put((request.name, "Connection"))
        self.sessions[request.room_name].notifications[request.name] = queue.Queue()
        return mafia_pb2.PlayersList(players=self.sessions[request.room_name].players_list)

    def NotificationStream(self, request, context):
        while True:
            if request.name not in self.sessions[request.room_name].notifications:
                continue
            else:
                name, notification = self.sessions[request.room_name].notifications[request.name].get()
                if name == request.name and notification == "Disconnection":
                    del self.sessions[request.room_name].notifications[request.name]
                    break
                yield mafia_pb2.Notifications(name=name, type=notification)

    def Disconnect(self, request, context):
        for notification in self.sessions[request.room_name].notifications:
            self.sessions[request.room_name].notifications[notification].put((request.name, "Disconnection"))
        if request.name in self.sessions[request.room_name].players_roles:
            self.sessions[request.room_name].roles = ["мафия", "комиссар", "мирный житель", "мирный житель"]
        self.sessions[request.room_name].players_list.remove(request.name)
        return mafia_pb2.Empty()

    def StartGame(self, request, context):
        with self.sessions[request.room_name].cv:
            self.sessions[request.room_name].ready_cnt += 1
            while self.sessions[request.room_name].ready_cnt < 4:
                self.sessions[request.room_name].cv.wait()
                if self.sessions[request.room_name].ready_cnt == 0:
                    break
            shuffle(self.sessions[request.room_name].roles)
            role = self.sessions[request.room_name].roles.pop()
            self.sessions[request.room_name].players_roles[request.name] = role
            self.sessions[request.room_name].ready_cnt = 0
            self.sessions[request.room_name].cv.notify()
        return mafia_pb2.StartGameResponse(players=self.sessions[request.room_name].players_list, role=role)

    def Ready(self, request, context):
        self.sessions[request.room_name].barrier.wait()
        return mafia_pb2.Empty()

    def SendVote(self, request, context):
        self.sessions[request.room_name].votes[request.vote] += 1
        self.sessions[request.room_name].barrier.wait()
        killed_player = max(self.sessions[request.room_name].votes, key=self.sessions[request.room_name].votes.get)
        print("Выбрали - ", killed_player)
        if self.sessions[request.room_name].votes[killed_player] == 1:
            killed_player = ""
        killed_role = ""
        if killed_player in self.sessions[request.room_name].players_roles:
            killed_role = self.sessions[request.room_name].players_roles[killed_player]
        self.sessions[request.room_name].barrier.wait()
        print("Выбрали - ", killed_role)
        self.sessions[request.room_name].votes.clear()
        self.sessions[request.room_name].players_roles[killed_player] = "наблюдатель"
        return mafia_pb2.VoteResponse(player=killed_player,
                                      role=killed_role)

    def MafiaChoice(self, request, context):
        if request.vote != "":
            self.sessions[request.room_name].last_killed = request.vote
        self.sessions[request.room_name].barrier.wait()
        killed_role = self.sessions[request.room_name].players_roles[self.sessions[request.room_name].last_killed]
        self.sessions[request.room_name].barrier.wait()
        self.sessions[request.room_name].players_roles[self.sessions[request.room_name].last_killed] = "наблюдатель"
        return mafia_pb2.VoteResponse(player=self.sessions[request.room_name].last_killed, role=killed_role)

    def CommissionerChoice(self, request, context):
        if request.vote != "":
            self.sessions[request.room_name].last_checked = request.vote
        self.sessions[request.room_name].barrier.wait()
        checked_role = self.sessions[request.room_name].players_roles[self.sessions[request.room_name].last_checked]
        self.sessions[request.room_name].barrier.wait()
        return mafia_pb2.VoteResponse(player=self.sessions[request.room_name].last_checked, role=checked_role)

    def AlivePlayers(self, request, context):
        alive_players = list()
        for player in self.sessions[request.room_name].players_list:
            if self.sessions[request.room_name].players_roles[player] != "наблюдатель":
                alive_players.append(player)
        return mafia_pb2.PlayersList(players=alive_players)

    def MafiaPlayers(self, request, context):
        mafia_players = list()
        for player in self.sessions[request.room_name].players_list:
            if self.sessions[request.room_name].players_roles[player] == "мафия":
                mafia_players.append(player)
        return mafia_pb2.PlayersList(players=mafia_players)
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    mafia_pb2_grpc.add_SoaMafiaServerServicer_to_server(
        SoaMafiaServer(), server)
    server.add_insecure_port('[::]:8080')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    serve()
