# server.py

import socket
import threading
import numpy as np
import idan_protocol as idp
import random as rnd

# Global variables
clients = []
clients_in_game = []

# Constants
ROWS = 15
COLS = 15
CELL_SIZE = 40
GRID_WIDTH = COLS * CELL_SIZE
GRID_HEIGHT = ROWS * CELL_SIZE
RED = (255, 0, 0)
BLUE = (0, 0, 255)


def notify_winner(arr, num, client1, client2):
    """
    Process: Notify clients of the winner if a winner was found
    :parameter: arr (numpy array), num (player's number), client1, client2
    :return: If a winner was found and successfully notified clients of the winner, Return true. Otherwise False
    """

    if check_death(arr, num):
        if num == 1:
            client1[1].send(idp.create_msg(f"victory:{client2[0]}"))
            client2[1].send(idp.create_msg(f"victory:{client2[0]}"))
        elif num == 2:
            client1[1].send(idp.create_msg(f"victory:{client1[0]}"))
            client2[1].send(idp.create_msg(f"victory:{client1[0]}"))

        clients_in_game.remove(client1)
        clients_in_game.remove(client2)
        broadcast_clients()
        return True
    return False


def check_death(arr, num):
    """
    Process: check if player lost by getting blocked or other player winning over half of the blocks
    :parameter: arr (numpy array), num (player's number)
    :return: True if player can move right, otherwise False
    """
    head_num = num + 2
    head_r, head_c = -1, -1

    for r in range(ROWS):
        for c in range(COLS):
            if arr[r, c] == head_num:
                head_r, head_c = r, c
                break

    # check if the head is blocked from all sides
    if ((head_c - 1 < 0 or arr[head_r, head_c - 1] != 0) and
            (head_c + 1 >= COLS or arr[head_r, head_c + 1] != 0) and
            (head_r - 1 < 0 or arr[head_r - 1, head_c] != 0) and
            (head_r + 1 >= ROWS or arr[head_r + 1, head_c] != 0)):
        return True

    # starting with 1 as both necessarily have one head block
    count_1 = 1
    count_2 = 1

    # check how many blocks each player controls
    for r in range(ROWS):
        for c in range(COLS):
            if arr[r, c] == 1:
                count_1 += 1
            elif arr[r, c] == 2:
                count_2 += 1

    if num == 1 and (count_2 > (ROWS * COLS) // 2):
        return True
    elif num == 2 and (count_1 > (ROWS * COLS) // 2):
        return True

    return False


def check_left(arr, num):
    """
    Process: If possible move left and return True to show a successful operation
    :parameter: arr (numpy array), num (player's number)
    :return: True if player can move left, otherwise False
    """

    # the head is recognized as the number of the player + 2
    head_num = num + 2
    head_r, head_c = -1, -1

    for r in range(ROWS):
        for c in range(COLS):
            if arr[r, c] == head_num:
                head_r, head_c = r, c
                break

    if head_c-1 >= 0 and arr[head_r, head_c-1] == 0:
        # set the new head pos, and the last head pos becomes numbered by the p_num, a "trail"
        arr[head_r, head_c-1] = head_num
        arr[head_r, head_c] = num
        return True
    else:
        return False


def check_right(arr, num):
    """
    Process: If possible move right and return True to show a successful operation
    :parameter: arr (numpy array), num (player's number)
    :return: True if player can move right, otherwise False
    """

    # the head is recognized as the number of the player + 2
    head_num = num + 2
    head_r, head_c = -1, -1

    for r in range(ROWS):
        for c in range(COLS):
            if arr[r, c] == head_num:
                head_r, head_c = r, c
                break

    if head_c + 1 <= 14 and arr[head_r, head_c + 1] == 0:
        # set the new head pos, and the last head pos becomes numbered by the p_num, a "trail"
        arr[head_r, head_c + 1] = head_num
        arr[head_r, head_c] = num
        return True
    else:
        return False


def check_up(arr, num):
    """
    Process: If possible move up and return True to show a successful operation
    :parameter: arr (numpy array), num (player's number)
    :return: True if player can move up, otherwise False
    """

    # the head is recognized as the number of the player + 2
    head_num = num + 2
    head_r, head_c = -1, -1

    for r in range(ROWS):
        for c in range(COLS):
            if arr[r, c] == head_num:
                head_r, head_c = r, c
                break

    if head_r - 1 >= 0 and arr[head_r-1, head_c] == 0:
        # set the new head pos, and the last head pos becomes numbered by the p_num, a "trail"
        arr[head_r-1, head_c] = head_num
        arr[head_r, head_c] = num
        return True
    else:
        return False


def check_down(arr, num):
    """
    Process: If possible move down and return True to show a successful operation
    :parameter: arr (numpy array), num (player's number)
    :return: True if player can move down, otherwise False
    """

    # the head is recognized as the number of the player + 2
    head_num = num + 2
    head_r, head_c = -1, -1

    for r in range(ROWS):
        for c in range(COLS):
            if arr[r, c] == head_num:
                head_r, head_c = r, c
                break

    if head_r + 1 <= 14 and arr[head_r+1, head_c] == 0:
        # set the new head pos, and the last head pos becomes numbered by the p_num, a "trail"
        arr[head_r+1, head_c] = head_num
        arr[head_r, head_c] = num
        return True
    else:
        return False


def setup_game():
    """
    Process: Create a numpy array of zeros and then add 3 and 4 as the heads of the players in random positions
    :parameter: Nothing
    :return: arr (numpy arr)
    """

    # create the array
    arr = np.zeros((ROWS, COLS), dtype=int)

    # place p1 head
    rand_r, rand_c = rnd.randint(0, 14), rnd.randint(0, 14)
    arr[rand_r, rand_c] = 3

    # place p2 head, in a pos that is not p1's (initiate this do-while mechanism for it)
    while True:
        rand_r, rand_c = rnd.randint(0, 14), rnd.randint(0, 14)
        if arr[rand_r, rand_c] == 0:
            arr[rand_r, rand_c] = 4
            break
    return arr


def handle_games(client1, client2):
    """
    Process: Send the updated client names to all clients
    :parameter: client1, client2 (sockets)
    :return: Nothing
    """

    global clients_in_game

    # send the players numbers, set up the initial board and start with player1's turn
    client1[1].send(idp.create_msg(f"p_num:{1}"))
    client2[1].send(idp.create_msg(f"p_num:{2}"))

    arr = setup_game()
    client1[1].send(idp.create_msg(f"update_arr:{idp.array_to_string(arr)}"))
    client2[1].send(idp.create_msg(f"update_arr:{idp.array_to_string(arr)}"))

    client1[1].send(idp.create_msg(f"do_turn"))
    turn_of_player = 1

    while True:
        # receive information from both clients, mostly the moves but also detect if a client has disconnected mid-game
        get_data1 = idp.get_msg(client1[1], 0.3)
        data1 = ""
        if get_data1[0]:
            data1 = get_data1[1]

        get_data2 = idp.get_msg(client2[1], 0.3)
        data2 = ""
        if get_data2[0]:
            data2 = get_data2[1]

        # if one client decided to disconnect mid-game notify the other and close the game for both
        if data1 == "forced_quit":
            client1[1].send(idp.create_msg("disconnected"))
            client2[1].send(idp.create_msg("other_disconnected"))
            clients_in_game.remove(client1)
            clients_in_game.remove(client2)
            broadcast_clients()
            break

        if data2 == "forced_quit":
            client1[1].send(idp.create_msg("other_disconnected"))
            client2[1].send(idp.create_msg("disconnected"))
            clients_in_game.remove(client1)
            clients_in_game.remove(client2)
            broadcast_clients()
            break

        # handle the data for the turn of player 1 or 2 depending on whose turn is it
        if turn_of_player == 1:
            # check if client was blocked in the other player's turn
            if notify_winner(arr, 1, client1, client2):
                break

            # if the move is valid update the game array and start the other player's turn
            if data1.startswith("move"):
                result = False
                _, direction = data1.split(':')

                if direction.__eq__("LEFT"):
                    result = check_left(arr, 1)
                elif direction.__eq__("RIGHT"):
                    result = check_right(arr, 1)
                elif direction.__eq__("UP"):
                    result = check_up(arr, 1)
                elif direction.__eq__("DOWN"):
                    result = check_down(arr, 1)

                if result:
                    client1[1].send(idp.create_msg("turn_done"))

                    client1[1].send(idp.create_msg(f"update_arr:{idp.array_to_string(arr)}"))
                    client2[1].send(idp.create_msg(f"update_arr:{idp.array_to_string(arr)}"))

                    # check if blocked himself during his turn
                    if notify_winner(arr, 1, client1, client2):
                        break

                    turn_of_player = 2
                    client2[1].send(idp.create_msg(f"do_turn"))

        elif turn_of_player == 2:
            # check if client was blocked in the other player's turn
            if notify_winner(arr, 2, client1, client2):
                break

            # if the move is valid update the game array and start the other player's turn
            if data2.startswith("move"):

                result = False
                _, direction = data2.split(':')

                if direction.__eq__("LEFT"):
                    result = check_left(arr, 2)
                elif direction.__eq__("RIGHT"):
                    result = check_right(arr, 2)
                elif direction.__eq__("UP"):
                    result = check_up(arr, 2)
                elif direction.__eq__("DOWN"):
                    result = check_down(arr, 2)

                if result:
                    client2[1].send(idp.create_msg("turn_done"))

                    client1[1].send(idp.create_msg(f"update_arr:{idp.array_to_string(arr)}"))
                    client2[1].send(idp.create_msg(f"update_arr:{idp.array_to_string(arr)}"))

                    # check if blocked himself during his turn
                    if notify_winner(arr, 2, client1, client2):
                        break

                    turn_of_player = 1
                    client1[1].send(idp.create_msg(f"do_turn"))


def broadcast_clients():
    """
    Process: Send the updated client names to all clients
    :parameter: Nothing
    :return: Nothing
    """

    global clients

    client_names = []

    for client in clients:
        if client not in clients_in_game:
            client_names.append(client[0])

    for client in clients:
        client_conn = client[1]
        client_conn.send(idp.create_msg(f"clients:{','.join(client_names)}"))


def handle_client(client_conn, addr):
    """
    Process: Initialize the server and accept new client connections
    :parameter: Client_conn, addr
    :return: Nothing
    """

    global clients, clients_in_game

    # get client's name and show it to connected clients
    name = ""
    get_name = idp.get_msg(client_conn)
    if get_name[0]:
        name = get_name[1]
    clients.append((name, client_conn))
    print(f"New connection: {name} ({addr[0]}:{addr[1]})")
    broadcast_clients()  # Notify all clients about new connection

    try:
        while True:
            # check if client in game
            client_playing = False
            for client in clients_in_game:
                if client[1] == client_conn:
                    client_playing = True

            # handle lobby matters
            if not client_playing:
                get_data = idp.get_msg(client_conn)
                data = ""
                if get_data[0]:
                    data = get_data[1]

                # if there is no data assume the client has disconnected
                if not data:
                    print(f"{name} disconnected.")
                    clients.remove((name, client_conn))
                    broadcast_clients()  # Notify all clients about disconnection
                    break

                # send game request
                elif data.startswith("request"):
                    _, opponent = data.split(":")
                    for client in clients:
                        if client[0] == opponent:
                            opponent_conn = client[1]
                            opponent_conn.send(idp.create_msg(f"request:{name}"))

                # if game accepted add the 2 client into a game together
                elif data.startswith("accept"):
                    _, requester = data.split(":")
                    save_client1 = None
                    save_client2 = None
                    for client in clients:
                        if client[1] == client_conn:
                            clients_in_game.append(client)
                            save_client1 = client
                            break

                    opponent_conn = None
                    for client in clients:
                        if client[0] == requester:
                            opponent_conn = client[1]
                            clients_in_game.append(client)
                            save_client2 = client
                            break

                    # check if the client who requested the game exited the lobby before the other client accepted
                    # the request, if so then don't enter a game
                    if opponent_conn is None:
                        clients_in_game.remove(save_client1)
                        if None in clients_in_game:
                            clients_in_game.remove(None)
                        continue

                    broadcast_clients()  # Notify all clients about new matches

                    # notify client of the game's beginning and start the game thread
                    client_conn.send(idp.create_msg(f"start_game"))
                    opponent_conn.send(idp.create_msg(f"start_game"))

                    threading.Thread(target=handle_games, args=(save_client1, save_client2)).start()

    except ConnectionResetError:
        # it will reach here when can't reach data, therefore the server realizes the client left
        # and remove him from the lobby
        print(f"{name} forcibly disconnected.")
        clients.remove((name, client_conn))
        broadcast_clients()  # Notify all clients about disconnection


def start_server():
    """
    Process: Initialize the server and accept new client connections
    :parameter: Nothing
    :return: Nothing
    """

    # set up the server socket, listen(5) as 5 is a reasonable value for the
    # unaccepted connections that the system will allow before refusing new connections.
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 12345))
    server.listen(5)

    print("Server started. Waiting for connections...")

    # as long as the server is up accept all connections and communicate with each client using a thread
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()


if __name__ == "__main__":
    start_server()
