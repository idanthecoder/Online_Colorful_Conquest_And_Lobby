# client.py

import socket
import threading
import time
from tkinter import messagebox, Listbox, END, SINGLE, simpledialog
from tkinter import *
import idan_protocol as idp
from functools import partial
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
LIGHT_GRAY = (211, 211, 211)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


def write_to_screen(text, font_size, x_pos, y_pos, color):
    """
    Process: Print a message on the pygame screen
    :parameter: text (string), font_size (int), x_pos (int), y_pos (int), color (tup[int])
    :return: Nothing
    """

    # Set up the screen dimensions
    screen_width, screen_height = 800, 600

    # Set up the font and size
    font = pygame.font.Font(None, font_size)

    # Render the text on a surface
    text_surface = font.render(text, True, color)

    # Clear the screen and draw the text
    win.fill(BLACK)
    win.blit(text_surface, (x_pos, y_pos))

    pygame.display.flip()


def recv_game_information():
    """
    Process: Receive game updates from the server and update the game state accordingly
    :parameter: Nothing
    :return: Nothing
    """

    global p_num, clients_turn, game_ended
    while True:
        get_data = idp.get_msg(client_socket)
        data = ""
        if get_data[0]:
            data = get_data[1]

        # receive data that will dictate screen update, if it's the client's turn and notify about the game's state
        if data.startswith("p_num"):
            _, num = data.split(':')
            p_num = int(num)
        elif data.startswith("update_arr"):
            _, str_arr = data.split(':')
            # use my protocol to get a numpy arr from string sent
            arr = idp.string_to_array(str_arr)
            draw_screen(arr)
        elif data == "do_turn":
            clients_turn = True
        elif data == "turn_done":
            clients_turn = False

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

            time.sleep(2)
            game_ended = True
            break
        elif data == "disconnected":
            game_ended = True
            break
        elif data == "other_disconnected":
            write_to_screen(f"Opponent disconnected", 50, GRID_WIDTH // 4, GRID_HEIGHT // 2, WHITE)
            time.sleep(2)
            game_ended = True
            break


def draw_screen(arr):
    """
    Process: Display the game board to the player
    :parameter: Arr of type numpy array
    :return: Nothing
    """

    global win
    # clear the screen
    win.fill(WHITE)

    # fill in the colors
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
                color = BLACK

            pygame.draw.rect(win, color, (c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    # generate a grid
    for r in range(0, GRID_WIDTH, CELL_SIZE):
        for c in range(0, GRID_HEIGHT, CELL_SIZE):
            rectangle = pygame.Rect(r, c, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(win, LIGHT_GRAY, rectangle, 1)

    pygame.display.flip()


def handle_game():
    """
    Process: Send player's moves to the server so that he may update the game accordingly
    :parameter: Nothing
    :return: Nothing
    """

    global p_num, win, clients_turn, game_ended

    pygame.init()
    win = pygame.display.set_mode((GRID_WIDTH, GRID_HEIGHT))
    pygame.display.set_caption("Colorful Conquest")
    play("assets/Resolute Hub.mp3")

    # start a thread that will receive game information from the server simultaneously to sending the player's moves
    threading.Thread(target=recv_game_information).start()

    get_key_input = True
    while True:
        if game_ended:
            pygame.quit()
            break
        if get_key_input:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # notify the server about the client's decision to exit mid-game
                    client_socket.send(idp.create_msg("forced_quit"))
                    pygame.quit()
                    get_key_input = False
                    break

                # receive data from the keyboard buffer and send it to the server if it's the player's turn
                if get_key_input and clients_turn and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        client_socket.send(idp.create_msg(f"move:LEFT"))
                    elif event.key == pygame.K_RIGHT:
                        client_socket.send(idp.create_msg(f"move:RIGHT"))
                    elif event.key == pygame.K_UP:
                        client_socket.send(idp.create_msg(f"move:UP"))
                    elif event.key == pygame.K_DOWN:
                        client_socket.send(idp.create_msg(f"move:DOWN"))


def send_request():
    """
    Process: Send the game request to the server so that he may transfer it to the other client
    :parameter: Nothing
    :return: Nothing
    """
    opponent = user_listbox.get(user_listbox.curselection())
    try:
        client_socket.send(idp.create_msg(name))  # Send the name to the server
        client_socket.send(idp.create_msg(f"request:{opponent}"))  # Send a game request to the server

    except ConnectionRefusedError:
        messagebox.showinfo("Server Error", "Server is not running.")


def on_closing():
    """
    Process: Terminate every ongoing activity
    :parameter: Nothing
    :return: Nothing
    """
    # close the window
    root.destroy()

    # close the socket
    client_socket.shutdown(socket.SHUT_RDWR)
    client_socket.close()
    exit(0)


def update_user_list(clients_response):
    """
    Process: Updates the clients list shown to the client
    :parameter: Clients_response (the server's message)
    :return: Nothing
    """
    clients_list = clients_response.split(":")[1]
    user_listbox.delete(0, END)
    for client in clients_list.split(","):
        if client != name:
            user_listbox.insert(END, client)


def start_client():
    """
    Process: The main lobby's function. Takes care of receiving data from the server and acting accordingly
    :parameter: Nothing
    :return: Nothing
    """
    global opponent, game_ended
    try:
        client_socket.send(idp.create_msg(name))  # Send the name to the server

        while True:
            # constantly receive data from the server using my protocol
            get_data = idp.get_msg(client_socket)
            data = ""
            if get_data[0]:
                data = get_data[1]

            # check for certain datas and respond accordingly
            if data.startswith("clients:"):
                update_user_list(data)
            elif data.startswith("request"):
                _, requester = data.split(":")
                if requester != name:
                    opponent = requester  # Store the requester's name for the current request
                    response = messagebox.askquestion("Game Request", f"Received game request from {requester}. Accept?")
                    if response == 'yes':
                        # Send the "accept" response to the server with the client's opponent
                        client_socket.send(idp.create_msg(f"accept:{opponent}"))
            elif data == "start_game":
                # halt everything tkinter (lobby) wise
                stop_music()
                root.withdraw()
                game_ended = False

                # call the function that will handle the game between the 2 clients
                handle_game()

                # get back to the lobby after the game has ended
                root.deiconify()

    except ConnectionRefusedError:
        messagebox.showinfo("Server Error", "Server is not running.")


def setup_music():
    """
    Process: Creates 2 button play and stop that will take care of the lobby's music
    :parameter: Nothing
    :return: Nothing
    """
    # use partial functions to set up the music buttons
    music_func = partial(play, "assets/Lounge Lizard.mp3")
    play_button = Button(root, text="Play some music!", font=("Helvetica", 20), command=music_func)
    play_button.pack(pady=10)

    stop_music_func = partial(stop_music, )
    stop_button = Button(root, text="Stop the music", font=("Helvetica", 20), command=stop_music_func)
    stop_button.pack(pady=10)


def play(directory):
    """
    Process: Initializes mixer and plays the audio in the directory
    :parameter: Directory of audio file
    :return: Nothing
    """
    pygame.mixer.init()
    try:
        pygame.mixer.music.load(directory)
        pygame.mixer.music.play(loops=-1)  # will loop indefinitely
    except pygame.error:
        pass


def stop_music():
    """
    Process: Stops mixer if initialized
    :parameter: Nothing
    :return: Nothing
    """
    try:
        pygame.mixer.music.stop()
    except pygame.error:
        pass


if __name__ == "__main__":
    # Global variables
    p_num = 0
    win = None
    clients_turn = False
    game_ended = False

    root = Tk()
    width = 800
    height = 600
    root.geometry(f"{width}x{height}")
    root.title("Multiplayer Lobby")
    root.protocol("WM_DELETE_WINDOW", on_closing)

    title = Label(root, text="WELCOME TO THE LOBBY!", bd=9, relief=GROOVE,
                  font=("times new roman", 40, "bold"), bg="white", fg="green")
    title.pack(side=TOP, fill=X)

    # get valid name from user
    name = None
    while name is None or name == "" or ':' in name or ',' in name:
        name = simpledialog.askstring("Username", "Enter your name:")
        if name is None:
            root.destroy()  # Close the window if the user clicks Cancel
            exit(0)

    # connect to the server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 12345))

    # Create the listbox to display connected users
    user_listbox = Listbox(root, selectmode=SINGLE)
    user_listbox.pack()

    # Create the send request button
    send_button = Button(root, text="Send Request", command=send_request)
    send_button.pack()

    # set up music buttons using tkinter and pygame's mixer
    setup_music()

    title = Label(root, text="Made by Idan Barkin", bd=9, relief=GROOVE,
                  font=("times new roman", 30, "bold"), bg="white", fg="green")
    title.pack()

    # start client thread, that will run simultaneously with the tkinter mainloop
    threading.Thread(target=start_client).start()

    root.mainloop()
