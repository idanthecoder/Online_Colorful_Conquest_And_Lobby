import socket
import os
import pickle
import sys
import numpy as np

LENGTH_FIELD_SIZE = 4
PORT = 8820


def create_msg(data):
    """
    Create a valid protocol message, with length field
    """
    # .send is sending information to the server
    # .encode is transforming string into bytes (necessary)
    data = str(data)
    data_length = str(len(data))
    zfill_data_length = str(data_length.zfill(LENGTH_FIELD_SIZE))
    reply = zfill_data_length + data

    return reply.encode()


def get_msg(my_socket):
    """
    Extract message from protocol, without the length field
    If length field does not include a number, returns False, "Error"
    """
    # .recv (receive) is getting information from the server
    # .decode is transforming bytes into string (necessary because everything coming out of socket will be bytes)
    data_length = my_socket.recv(LENGTH_FIELD_SIZE).decode()
    if data_length.isnumeric():
        data = my_socket.recv(int(data_length)).decode()
        return True, data
    return False, "Error"


def array_to_string(arr):
    return str(arr)


def string_to_array(str_arr):
    # Removing unwanted characters and converting the string to a 1D array
    str_arr = str_arr.replace('[', '').replace(']', '').replace('\n', '')
    one_d_array = np.fromstring(str_arr, dtype=int, sep=' ')

    # Reshaping the 1D array into a 2D array
    rows, cols = 15, 15
    two_d_array = one_d_array.reshape((rows, cols))
    return two_d_array
