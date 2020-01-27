# pylint: disable=no-self-use, missing-docstring, inconsistent-return-statements, too-few-public-methods
# pylint: disable=too-many-instance-attributes
import os

from tkinter import Tk, Frame, StringVar, Text, OptionMenu, Radiobutton, IntVar, Button, Entry, W
from tkinter import constants

from igutils.common.player.poker_user import PokerUser
from igutils.db.tournament import Tournament


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_DIR = os.path.join(ROOT_DIR, '..\\..', 'environments')


class View:
    def __init__(self, controller, model, root):
        root.wm_title("Finish player in tournament")
        self.controller = controller
        self.model = model
        self.list_of_environments = self.model.get_list_of_environments()
        self.buttons = []
        self.top_frame = Frame(root)
        self.top_frame.pack()
        self.right_frame = Frame(root, bd=20)
        self.right_frame.pack(side=constants.RIGHT)

        self.bottom_frame = Frame(root)
        self.bottom_frame.pack()
        self.bottom_frame_text = Frame(root)
        self.bottom_frame_text.pack(side=constants.BOTTOM)

        self.message = Text(self.bottom_frame_text, height=1, width=50)
        self.message.pack()
        self.__show_text_in_message_box("Enter Tournament ID")

        self.var_select_env = StringVar(self.top_frame)
        self.var_select_env.set(self.list_of_environments[0])
        self.option = OptionMenu(self.top_frame, self.var_select_env, *self.list_of_environments)
        self.option.grid(row=1, column=1)
        self.var_select_env.trace('w', self.__change_environment)

        self.refresh = Button(self.top_frame, text='Refresh', command=self.__refresh_players)
        self.refresh.grid(row=1, column=2)
        self.__disable_button(self.refresh)

        self.top_frame.grid_columnconfigure(3, minsize=80)

        self.entry = Entry(self.top_frame, width=12)
        self.entry.grid(row=1, column=4)

        self.enter_tour_id = Button(self.top_frame, text='Change Tour ID', command=self.__change_tour_id)
        self.enter_tour_id.grid(row=1, column=5)

        self.evict_all_players = Button(self.top_frame, text='Evict All', command=self.__evict_all)
        self.evict_all_players.grid(row=1, column=6)
        self.__disable_button(self.evict_all_players)

        self.var = IntVar()
        self.var.set(1)
        Radiobutton(self.right_frame, text="Players Name", variable=self.var, value=1, command=self.refresh_view).\
            pack(anchor=W)
        Radiobutton(self.right_frame, text="Players Nickname", variable=self.var, value=2, command=self.refresh_view).\
            pack(anchor=W)
        Radiobutton(self.right_frame, text="Players ID", variable=self.var, value=3, command=self.refresh_view).\
            pack(anchor=W)
        Radiobutton(self.right_frame, text="Players chips", variable=self.var, value=4, command=self.refresh_view).\
            pack(anchor=W)

    def __show_text_in_message_box(self, text):
        self.message.config(state=constants.NORMAL)
        self.message.delete(1.0, constants.END)
        self.message.insert(constants.END, text)
        self.message.config(state=constants.DISABLED)

    def __draw_buttons(self, list_of_players_id):
        column_x = 0
        row_y = 0
        count = 0
        choice = self.var.get()
        text = ''
        for player_id in list_of_players_id:
            if choice == 1:
                text = self.model.get_player_name(player_id)
            elif choice == 2:
                text = self.model.get_player_nick_name(player_id)
            elif choice == 3:
                text = player_id
            elif choice == 4:
                text = int(self.model.get_player_chips(player_id))

            evict_button = Button(self.bottom_frame, text=text, width=10, fg="purple",
                                  command=lambda num=count: self.__evict_player(list_of_players_id[num],
                                                                                self.buttons[num]))
            self.buttons.append(evict_button)
            evict_button.grid(row=row_y, column=column_x)

            if column_x == 9:
                column_x = 0
                row_y += 1
            else:
                column_x += 1

            count += 1

    def __destroy_buttons(self):
        for button in self.buttons:
            button.destroy()

        self.buttons = []

    def refresh_view(self):
        self.entry.delete(0, constants.END)
        self.__destroy_buttons()
        list_of_players_id = self.model.get_list_of_players_id()
        tour_id = self.model.get_tour_id()
        if tour_id == 0:
            self.__disable_button(self.refresh)
            self.__disable_button(self.evict_all_players)
            self.__show_text_in_message_box("Enter Tournament ID")
        else:
            self.__enable_button(self.refresh)
            self.entry.insert(0, tour_id)
            if list_of_players_id:
                self.__draw_buttons(list_of_players_id)
                self.__enable_button(self.evict_all_players)
                self.__show_text_in_message_box("Click on player button to evict player.")
            else:
                self.__disable_button(self.evict_all_players)
                self.__show_text_in_message_box("There is no active players!")

    def __disable_button(self, button):
        button.config(state='disable')

    def __enable_button(self, button):
        button.config(state='normal')

    def __refresh_players(self):
        self.controller.refresh_model_view()

    def __change_tour_id(self):
        try:
            tour_id = int(self.entry.get())
        except ValueError:
            self.__show_text_in_message_box("Invalid input!!! Please enter valid ID!")
            return -1
        if tour_id > 0:
            self.controller.change_tour_id(tour_id)
        else:
            self.__show_text_in_message_box("Incorrect tournament ID!!! Please enter valid ID!")

    def __change_environment(self, *args):
        self.controller.change_environment(self.var_select_env.get())

    def __evict_player(self, player_id, button):
        self.controller.evict_player(player_id)
        self.__disable_button(button)
        self.__show_text_in_message_box('The player will be evicted after current hand.')

    def __evict_all(self):
        self.controller.evict_all()
        self.__disable_button(self.evict_all_players)
        for button in self.buttons:
            self.__disable_button(button)
        self.__show_text_in_message_box('All players will be evicted after current hand.')


class Model:
    def __init__(self):
        self.__list_of_environments = []
        self.__current_env_name = None
        self.__load_list_of_environments()
        self.__list_of_players_id = []
        self.__list_of_players = {}
        self.__players_chip = {}
        self.__tournament_id = 0
        self.tournament = None

    def update_players(self):
        self.clear_players()
        self.tournament = Tournament(self.__tournament_id)
        list_of_players = self.tournament.get_players_list()
        if list_of_players:
            self.set_list_of_players_id([player.TUD_UserID for player in list_of_players])
            self.set_player_chips({player.TUD_UserID: player.TUD_Chips for player in list_of_players})
        self.load_players_info()

    def load_players_info(self):
        self.__list_of_players = {}
        if self.__tournament_id > 0:
            for player_id in self.__list_of_players_id:
                self.__list_of_players[player_id] = (PokerUser(player_id,))

    def __load_list_of_environments(self):
        files = os.listdir(ENV_DIR)
        for file in files:
            if '.json' in file:
                self.__list_of_environments.append(file.split('.json')[0])
        self.set_current_env_name(self.__list_of_environments[0])

    def get_list_of_environments(self):
        return self.__list_of_environments

    def set_current_env_name(self, current_env_name):
        self.__current_env_name = current_env_name
        self.set_ig_host_environment_variable(current_env_name)

    def get_current_env_name(self):
        return self.__current_env_name

    def set_tour_id(self, tour_id):
        self.__tournament_id = tour_id

    def get_tour_id(self):
        return self.__tournament_id

    def get_list_of_players_id(self):
        return self.__list_of_players_id

    def get_player_name(self, player_id):
        return self.__list_of_players[player_id].name

    def get_player_nick_name(self, player_id):
        return self.__list_of_players[player_id].nickname

    def get_player_chips(self, player_id):
        return self.__players_chip[player_id]

    def set_list_of_players_id(self, list_of_players_id):
        self.__list_of_players_id = list_of_players_id

    def set_player_chips(self, player_chips):
        self.__players_chip = player_chips

    def clear_players(self):
        self.__list_of_players_id = []
        self.__list_of_players = {}
        self.__players_chip = {}

    @staticmethod
    def set_ig_host_environment_variable(value: str):
        os.environ["IG_HOST"] = value


class Controller:
    def __init__(self):
        self.model = Model()
        self.root = Tk()
        self.view = View(self, self.model, self.root)

    def change_environment(self, current_env):
        self.model.set_current_env_name(current_env)
        self.model.set_tour_id(0)
        self.model.clear_players()
        self.view.refresh_view()

    def change_tour_id(self, tour_id):
        self.model.set_tour_id(tour_id)
        self.refresh_model_view()

    def evict_all(self):
        self.model.tournament.evict_player(self.model.get_list_of_players_id())

    def evict_player(self, player):
        self.model.tournament.evict_player([player])

    def refresh_model_view(self):
        self.model.update_players()
        self.view.refresh_view()

    def start(self):
        self.root.mainloop()


if __name__ == '__main__':
    Controller().start()
