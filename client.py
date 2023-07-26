import socket
import threading
#import tkinter as tk
import time
from tkinter import messagebox, Listbox, END, SINGLE, simpledialog
from tkinter import *
import idan_protocol as idp
from functools import partial
#from game import *
import pygame

# Constants
ROWS = 15
COLS = 15
CELL_SIZE = 40
GRID_WIDTH = COLS * CELL_SIZE
GRID_HEIGHT = ROWS * CELL_SIZE
RED = (255, 0, 0)
BLUE = (0, 0, 255)
DARK_BLUE = (0, 0, 139)
DARK_RED = (139, 0, 0)
DARK_GRAY = (169, 169, 169)
LIGHT_GRAY = (211,211,211)


def write_to_screen(text, font_size, x_pos, y_pos, color):

    # Set up the screen dimensions
    screen_width, screen_height = 800, 600

    # Set up the font and size
    font = pygame.font.Font(None, font_size)

    # Render the text on a surface
    text_surface = font.render(text, True, color)

    # Clear the screen
    win.fill((0, 0, 0))

    # Draw the text on the screen
    win.blit(text_surface, (x_pos, y_pos))

    # Update the display
    pygame.display.flip()


def recv_game_information():
    global p_num, clients_turn, already_clicked, game_ended
    while True:
        get_data = idp.get_msg(client_socket)
        data = ""
        if get_data[0]:
            data = get_data[1]

        if data.startswith("p_num"):
            _, num = data.split(':')
            p_num = int(num)
        elif data.startswith("update_arr"):
            _, str_arr = data.split(':')
            arr = idp.string_to_array(str_arr)
            draw_screen(arr)
        elif data == "do_turn":
            clients_turn = True
            #already_clicked = False
        elif data == "turn_done":
            clients_turn = False
            #already_clicked = False
        elif data == "illegal_move":
            already_clicked = False

        #elif data.startswith("update_arr"):
        #    _, str_arr = data.split(':')
        #    arr = idp.string_to_array(str_arr)
        #    draw_screen(arr)

        elif data.startswith("victory"):
            _, victor = data.split(':')
            if victor == name:
                if p_num == 1:
                    write_to_screen(f"{victor} won the game!!", 50, GRID_WIDTH // 4, GRID_HEIGHT // 2, RED)
                elif p_num == 2:
                    write_to_screen(f"{victor} won the game!!", 50, GRID_WIDTH // 4, GRID_HEIGHT // 2, BLUE)
            else:
                if p_num == 1:
                    write_to_screen(f"{victor} won the game!!", 50, GRID_WIDTH // 4, GRID_HEIGHT // 2, BLUE)
                elif p_num == 2:
                    write_to_screen(f"{victor} won the game!!", 50, GRID_WIDTH // 4, GRID_HEIGHT // 2, RED)

            #print(f"{victor} won the game!!")

            time.sleep(2)
            game_ended = True
            break
        #elif data == "disconnected":
        #    break


def draw_screen(arr):
    global win
    win.fill((255, 255, 255))

    for r in range(ROWS):
        for c in range(COLS):
            if arr[r, c] == 1:
                color = RED
            elif arr[r, c] == 2:
                color = BLUE
            elif arr[r, c] == 3:
                color = DARK_RED
            elif arr[r, c] == 4:
                color = DARK_BLUE
            else:
                color = (0, 0, 0)

            pygame.draw.rect(win, color, (c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    for r in range(0, GRID_WIDTH, CELL_SIZE):
        for c in range(0, GRID_HEIGHT, CELL_SIZE):
            rectangle = pygame.Rect(r, c, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(win, LIGHT_GRAY, rectangle, 1)

    pygame.display.flip()


def handle_game():
    global p_num, win, clients_turn, already_clicked, game_ended

    pygame.init()
    win = pygame.display.set_mode((GRID_WIDTH, GRID_HEIGHT))
    pygame.display.set_caption("Game")

    threading.Thread(target=recv_game_information).start()

    #stop_loop = False
    while True:
        if game_ended:
            pygame.quit()
            break
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                #client_socket.send(idp.create_msg("forced_quit"))
                pygame.quit()
                #stop_loop = True
                break

            #if not already_clicked:
            if clients_turn and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    client_socket.send(idp.create_msg(f"move:LEFT"))
                    #already_clicked = True
                elif event.key == pygame.K_RIGHT:
                    client_socket.send(idp.create_msg(f"move:RIGHT"))
                    #already_clicked = True
                elif event.key == pygame.K_UP:
                    client_socket.send(idp.create_msg(f"move:UP"))
                    #already_clicked = True
                elif event.key == pygame.K_DOWN:
                    client_socket.send(idp.create_msg(f"move:DOWN"))
                    #already_clicked = True
        #if stop_loop:
        #    break


def send_request():
    opponent = user_listbox.get(user_listbox.curselection())
    try:
        client_socket.send(idp.create_msg(name))  # Send the name to the server
        client_socket.send(idp.create_msg(f"request:{opponent}"))  # Send a game request to the server

    except ConnectionRefusedError:
        messagebox.showinfo("Server Error", "Server is not running.")


def on_closing():
    #global this_client_matches

    #for match in this_client_matches:
    #    match.send(idp.create_msg("exit"))  # Notify the server about ending the game

    # i don't think this is necessary
    #client_socket.send(idp.create_msg("exit"))

    # close the window
    root.destroy()

    # close the socket
    client_socket.shutdown(socket.SHUT_RDWR)
    client_socket.close()
    exit(0)


def update_user_list(clients_response):
    clients_list = clients_response.split(":")[1]
    user_listbox.delete(0, END)
    for client in clients_list.split(","):
        if client != name:
            user_listbox.insert(END, client)


def start_client():
    global opponent, game_ended
    try:
        #client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #client_socket.connect(('localhost', 12345))

        client_socket.send(idp.create_msg(name))  # Send the name to the server

        while True:

            get_data = idp.get_msg(client_socket)
            data = ""
            if get_data[0]:
                data = get_data[1]

            if data.startswith("clients:"):
                update_user_list(data)
            elif data == "accept":
                messagebox.showinfo("Game Request", f"Game request accepted by {opponent}")
            elif data == "unavailable":
                messagebox.showinfo("Game Request", "Opponent is currently in a game.")
            elif data.startswith("request"):
                _, requester = data.split(":")
                if requester != name:
                    opponent = requester  # Store the requester's name for the current request
                    response = messagebox.askquestion("Game Request", f"Received game request from {requester}. Accept?")
                    if response == 'yes':
                        client_socket.send(idp.create_msg(f"accept:{opponent}"))  # Send the "accept" response to the server
            elif data == "start_game":
                stop_music()

                root.withdraw()

                game_ended = False

                handle_game()
                print("game done do deiconify")
                # get back to the lobby
                root.deiconify()

                #client_socket.send(idp.create_msg("finished_game"))

    except ConnectionRefusedError:
        messagebox.showinfo("Server Error", "Server is not running.")


def setup_music():
    music_func = partial(play, )
    play_button = Button(root, text="Play some music!", font=("Helvetica", 20), command=music_func)
    play_button.pack(pady=10)

    stop_music_func = partial(stop_music, )
    stop_button = Button(root, text="Stop the music", font=("Helvetica", 20), command=stop_music_func)
    stop_button.pack(pady=10)


def play():
    pygame.mixer.init()
    pygame.mixer.music.load("assets/lounge lizard pvz.mp3")
    pygame.mixer.music.play(loops=-1)  # will loop indefinitely


def stop_music():
    try:
        pygame.mixer.music.stop()
    except pygame.error:
        pass


if __name__ == "__main__":
    # Global variables
    p_num = 0
    win = None
    clients_turn = False
    already_clicked = False
    game_ended = False
    this_client_matches = set()
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 12345))

    root = Tk()
    width = 800
    height = 600
    root.geometry(f"{width}x{height}")
    root.title("Multiplayer Lobby")
    root.protocol("WM_DELETE_WINDOW", on_closing)

    title = Label(root, text="WELCOME TO THE LOBBY!", bd=9, relief=GROOVE,
                  font=("times new roman", 40, "bold"), bg="white", fg="green")
    title.pack(side=TOP, fill=X)

    name = simpledialog.askstring("Username", "Enter your name:")

    # Create the listbox to display connected users
    user_listbox = Listbox(root, selectmode=SINGLE)
    user_listbox.pack()

    # Create the send request button
    send_button = Button(root, text="Send Request", command=send_request)
    send_button.pack()

    setup_music()

    threading.Thread(target=start_client).start()

    root.mainloop()
