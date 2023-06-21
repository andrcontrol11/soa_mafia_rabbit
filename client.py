import random
import threading
import pika
import grpc
from protos import mafia_pb2
from protos import mafia_pb2_grpc

from rabbit.rabbit import RabbitClient, RabbitServer

class Client:
    def __init__(self):
        self.name = None
        self.room_name = None
        self.stub = None
        self.notification_stub = None
        self.chanel = grpc.insecure_channel('localhost:8080')
        self.chanel_for_notes = grpc.insecure_channel('localhost:8080')
        self.players_list = list()
        self.role = None
        self.auto = False
        self.days_cnt = 0
        self.civilians_cnt = 2
        self.commissioner_is_dead = False
        self.rabbit_client = None
        self.rabbit_server = RabbitServer()

    def start_concuming(self):
        print("Start listening")
        self.rabbit_client.channel.start_consuming()

    def chat(self, time="day"):
        if not self.auto and (time == "day" or (time == "night" and self.role == "мафия")):
            while True:
                texted = input()
                if texted == 'Ready':
                    break
                else:
                    texted = self.name + " : " + texted
                    texted = texted.encode(encoding='UTF-8', errors='replace')
                    self.rabbit_server.channel.basic_publish(
                        exchange='rabbit_server',
                        routing_key='rpc_queue',
                        body=texted,
                        properties=pika.BasicProperties(
                            headers={'name': str(self.name), 'room_name': str(self.room_name), 'time': time}))
        self.stub.Ready(mafia_pb2.Player(name=self.name, room_name=self.room_name))
        return
    def day(self, killed_player=None, killed_role=None, checked_player=None, checked_role=None):
        self.days_cnt += 1
        print("Город просыпается")
        if self.days_cnt == 1:
            print("В первый день голосование не проводится\n"
                  "Вы можете рассказать о себе и пообщаться используя игровой чат\n"
                  "После того, как все игроки будут готовы закончить первый день они должны ввести 'Ready'")
            self.chat()
            return self.night()
        print("Ночью был убит ", killed_player, "\nЕго роль была - ", killed_role)
        if killed_role == "мирный житель":
            self.civilians_cnt -= 1
            if self.civilians_cnt == 1:
                print("Мафия победила...")
                return
        elif checked_role == "мафия":
            print("Ночью комиссар проверил игрока ", checked_player, "\nОн оказался мафией!")
            print("Мирные жители победили!")
            return
        else:
            self.commissioner_is_dead = True
        self.players_list.remove(killed_player)
        if killed_player == self.name:
            self.role = "наблюдатель"
            self.auto = True
        if not self.auto:
            print("Перед голосованием игроки могу пообщаться в игровом чате")
            print("После того, как все игроки будут готовы закончить обсуждение они должны ввести 'Ready'")
            self.chat()
            print("Проголосуйте за игрока, которого хотите казнить")
        else:
            self.chat()
        vote = self.vote()
        print("Идет голосование...")
        response = self.stub.SendVote(
            mafia_pb2.Vote(name=self.name, room_name=self.room_name, vote=vote))
        killed_player = response.player
        if killed_player == "":
            print("Игроки не смогли сделать единогласный выбор")
        else:
            print("Игроки проголосовали за ", killed_player)
            print("У {} была роль - ".format(killed_player), response.role)
            if response.role == "мирный житель":
                self.civilians_cnt -= 1
                if self.civilians_cnt == 1:
                    print("Мафия победила...")
                    return
            elif response.role == "мафия":
                print("Мирные жители победили!")
                return
            else:
                self.commissioner_is_dead = True
            self.players_list.remove(killed_player)
            if killed_player == self.name:
                self.role = "наблюдатель"
        self.night()

    def night(self):
        print("Город засыпает")
        print("Просыпается мафия...")
        if self.role == "мирный житель" or self.role == "дух":
            self.chat("night")
            killed_player, killed_role = self.mafia_woke_up("")
            print("Мафия сделала свой выбор")

            if not self.commissioner_is_dead:
                print("Просыпается комиссар")

            checked_player, checked_role = self.commissioner_woke_up("")

            if not self.commissioner_is_dead:
                print("Комиссар сделал свой выбор")

            return self.day(killed_player, killed_role, checked_player, checked_role)
        elif self.role == "мафия":
            if not self.auto:
                print("Игроки с ролью мафия могу пообщаться в чате игры перед принятием решения")
                print("После того, как игроки будут готовы закончить обсуждение они должны ввести 'Ready'")
                self.chat("night")
                print("Выберите игрока, которого хотите убить")

            vote = self.vote()

            killed_player, killed_role = self.mafia_woke_up(vote)

            if not self.commissioner_is_dead:
                print("Просыпается комиссар")

            checked_player, checked_role = self.commissioner_woke_up("")

            if not self.commissioner_is_dead:
                print("Комиссар сделал свой выбор")

            return self.day(killed_player, killed_role, checked_player, checked_role)
        elif self.role == "комиссар":
            self.chat("night")
            killed_player, killed_role = self.mafia_woke_up("")

            print("Мафия сделала свой выбор")
            if not self.auto:
                print("Выберите игрока, которого хотите проверить")
            vote = self.vote()

            checked_player, checked_role = self.commissioner_woke_up(vote)
            return self.day(killed_player, killed_role, checked_player, checked_role)

    def vote(self):
        if self.auto:
            if self.role != "наблюдатель":
                print("Выбран автоматический режим, вы голосуете случайно...")
                while True:
                    vote = random.randint(0, len(self.players_list) - 1)
                    if self.players_list[vote] != self.name:
                        break
        else:
            for i, value in enumerate(self.players_list):
                if value == self.name:
                    continue
                print("Введите ", i, "если хотите выбрать ", value)
            vote = int(input())
        if self.role == "наблюдатель":
            vote = ""
        else:
            vote = self.players_list[vote]
            print("Вы выбрали - ", vote)
        return vote

    def mafia_woke_up(self, vote):
        response = self.stub.MafiaChoice(
            mafia_pb2.Vote(name=self.name, room_name=self.room_name, vote=vote))
        killed_player = response.player
        killed_role = response.role
        return killed_player, killed_role

    def commissioner_woke_up(self, vote):
        response = self.stub.CommissionerChoice(
            mafia_pb2.Vote(name=self.name, room_name=self.room_name, vote=vote))
        checked_player = response.player
        checked_role = response.role
        return checked_player, checked_role

    def notifications_stream(self):
        for notification in self.notification_stub.NotificationStream(
                mafia_pb2.Player(name=self.name, room_name=self.room_name)):
            if notification.type == "Connection":
                print(notification.name, " подключился к игре")
                self.players_list.append(notification.name)
            else:
                print(notification.name, " отключился от игры")
                if notification.name in self.players_list:
                    self.players_list.remove(notification.name)
        print("Bye bye!")
        self.chanel_for_notes.close()

    def run(self):
        while True:
            print("Введите имя пользователя(только на английском)")
            self.name = input()
            if self.name == "":
                print("Имя не может быть пустым")
            else:
                break
        self.stub = mafia_pb2_grpc.SoaMafiaServerStub(self.chanel)
        self.notification_stub = mafia_pb2_grpc.SoaMafiaServerStub(self.chanel_for_notes)
        while True:
            print("Введите имя комнаты(на английском или цифрами)")
            self.room_name = input()
            if self.room_name == "":
                print("Имя комнаты не может быть пустым")
            else:
                break
        response = self.stub.RegistratePlayer(mafia_pb2.Player(name=self.name, room_name=self.room_name))
        self.players_list = response.players
        thread = threading.Thread(target=self.notifications_stream)
        thread.start()
        self.rabbit_client = RabbitClient(self.name, self.room_name)
        thread2 = threading.Thread(target=self.start_concuming, args=())
        thread2.start()
        while True:
            print("Выберите действие:\n "
                  "'Leave' - для того, чтобы покинуть комнату\n"
                  "'Ready' - для того, чтобы подтвердить готовность и получить роль\n"
                  "'Players' - для того, чтобы просмотреть список подключившихся игроков")
            command = input().upper()
            if command == "LEAVE":
                self.stub.Disconnect(mafia_pb2.Player(name=self.name, room_name=self.room_name))
                break
            elif command == "READY":
                response = self.stub.StartGame(mafia_pb2.Player(name=self.name, room_name=self.room_name))
                print("Ваша роль - ", response.role)
                self.role = response.role
                self.players_list = response.players
                print(
                    "Выберите режим игры: 'Auto' для автоматического или  нажмите 'Enter' для того, чтобы играть самому")
                is_auto = input().upper()
                if is_auto == "AUTO":
                    self.auto = True
                self.day()
                self.stub.Disconnect(mafia_pb2.Player(name=self.name, room_name=self.room_name))
                self.rabbit_client.close()
                self.rabbit_server.close()
                break
            elif command == "PLAYERS":
                print(self.players_list)
            else:
                print("Введена не верная команда!")
        self.chanel.close()


if __name__ == '__main__':
    client = Client()
    client.run()
