# server.py

import socket
import threading
import numpy as np
import idan_protocol as idp
import random as rnd

# Global variables
clients = []
clients_in_game = []
pending_requests = []
matches = []

# Constants
ROWS = 15
COLS = 15
CELL_SIZE = 40
GRID_WIDTH = COLS * CELL_SIZE
GRID_HEIGHT = ROWS * CELL_SIZE
RED = (255, 0, 0)
BLUE = (0, 0, 255)


def check_death(arr, num):
    head_num = num + 2
    head_r, head_c = -1, -1

    for r in range(ROWS):
        for c in range(COLS):
            if arr[r, c] == head_num:
                head_r, head_c = r, c
                break

    if ((head_c - 1 < 0 or arr[head_r, head_c - 1] != 0) and
            (head_c + 1 >= COLS or arr[head_r, head_c + 1] != 0) and
            (head_r - 1 < 0 or arr[head_r - 1, head_c] != 0) and
            (head_r + 1 >= ROWS or arr[head_r + 1, head_c] != 0)):
        return True

    count_1 = 0
    count_2 = 0

    for r in range(ROWS):
        for c in range(COLS):
            if arr[r, c] == 1 or arr[r, c] == 3:
                count_1 += 1
            elif arr[r, c] == 2 or arr[r, c] == 4:
                count_2 += 1

    if num == 1 and (count_2 > (ROWS * COLS) // 2):
        return True
    elif num == 2 and (count_1 > (ROWS * COLS) // 2):
        return True

    return False


def check_left(arr, num):
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
    global clients_in_game

    client1[1].send(idp.create_msg(f"p_num:{1}"))
    client2[1].send(idp.create_msg(f"p_num:{2}"))

    arr = setup_game()
    client1[1].send(idp.create_msg(f"update_arr:{idp.array_to_string(arr)}"))
    client2[1].send(idp.create_msg(f"update_arr:{idp.array_to_string(arr)}"))

    client1[1].send(idp.create_msg(f"do_turn"))
    turn_of_player = 1

    while True:
        get_data1 = idp.get_msg(client1[1], 0.3)
        data1 = ""
        if get_data1[0]:
            data1 = get_data1[1]

        get_data2 = idp.get_msg(client2[1], 0.3)
        data2 = ""
        if get_data2[0]:
            data2 = get_data2[1]

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

        if turn_of_player == 1:
            if not data1:
                pass

            elif data1.startswith("move"):
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
                else:
                    pass

                if result:
                    client1[1].send(idp.create_msg("turn_done"))

                    client1[1].send(idp.create_msg(f"update_arr:{idp.array_to_string(arr)}"))
                    client2[1].send(idp.create_msg(f"update_arr:{idp.array_to_string(arr)}"))

                    if check_death(arr, 1):
                        client1[1].send(idp.create_msg(f"victory:{client2[0]}"))
                        client2[1].send(idp.create_msg(f"victory:{client2[0]}"))

                        clients_in_game.remove(client1)
                        clients_in_game.remove(client2)
                        broadcast_clients()
                        break
                    else:
                        turn_of_player = 2
                        client2[1].send(idp.create_msg(f"do_turn"))

                else:
                    client1[1].send(idp.create_msg("illegal_move"))

        elif turn_of_player == 2:
            if not data2:
                pass

            elif data2.startswith("move"):

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
                else:
                    pass

                if result:
                    client2[1].send(idp.create_msg("turn_done"))

                    client1[1].send(idp.create_msg(f"update_arr:{idp.array_to_string(arr)}"))
                    client2[1].send(idp.create_msg(f"update_arr:{idp.array_to_string(arr)}"))

                    if check_death(arr, 2):
                        client1[1].send(idp.create_msg(f"victory:{client1[0]}"))
                        client2[1].send(idp.create_msg(f"victory:{client1[0]}"))

                        clients_in_game.remove(client1)
                        clients_in_game.remove(client2)
                        broadcast_clients()
                        break
                    else:
                        turn_of_player = 1
                        client1[1].send(idp.create_msg(f"do_turn"))

                else:
                    client2[1].send(idp.create_msg("illegal_move"))


def broadcast_clients():
    global clients

    client_names = []

    for client in clients:
        if client not in clients_in_game:
            client_names.append(client[0])

    for client in clients:
        client_conn = client[1]
        client_conn.send(idp.create_msg(f"clients:{','.join(client_names)}"))


def handle_client(client_conn, addr):
    global clients, pending_requests, clients_in_game, matches

    name = ""
    get_name = idp.get_msg(client_conn)
    if get_name[0]:
        name = get_name[1]
    clients.append((name, client_conn))
    print(f"New connection: {name} ({addr[0]}:{addr[1]})")
    broadcast_clients()  # Notify all clients about new connection

    #client_playing = False
    try:
        while True:
            client_playing = False
            for client in clients_in_game:
                if client[1] == client_conn:
                    client_playing = True

            if not client_playing:
                get_data = idp.get_msg(client_conn)
                data = ""
                if get_data[0]:
                    data = get_data[1]

                if not data:
                    print(f"{name} disconnected.")
                    clients.remove((name, client_conn))
                    # maybe clients in game . remove ??
                    pending_requests = [req for req in pending_requests if req[0] != name]  # Remove from pending requests
                    broadcast_clients()  # Notify all clients about disconnection
                    break

                elif data.startswith("request"):
                    _, opponent = data.split(":")
                    for client in clients:
                        if client[0] == opponent:
                            pending_requests.append((name, client[1]))  # Add the pending request to the list
                            opponent_conn = client[1]
                            opponent_conn.send(idp.create_msg(f"request:{name}"))

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

                    pending_requests = [req for req in pending_requests if req[1] != client_conn]  # Remove from pending requests
                    broadcast_clients()  # Notify all clients about new matches

                    #matches.append((save_client1, save_client2))

                    client_conn.send(idp.create_msg(f"start_game"))
                    opponent_conn.send(idp.create_msg(f"start_game"))

                    threading.Thread(target=handle_games, args=(save_client1, save_client2)).start()

    except ConnectionResetError:
        # it will reach here when can't reach data, therefore the server realizes the client left and removed him from the lobby
        print(f"{name} forcibly disconnected.")
        clients.remove((name, client_conn))
        # ??? clients_in_game.remove((name, client_conn))  # Remove from matches if present
        pending_requests = [req for req in pending_requests if req[0] != name]  # Remove from pending requests
        broadcast_clients()  # Notify all clients about disconnection


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 12345))
    server.listen(5)

    print("Server started. Waiting for connections...")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()


if __name__ == "__main__":
    start_server()
