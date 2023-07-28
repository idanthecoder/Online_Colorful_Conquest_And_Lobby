# idan_protocol.py
import socket
import numpy as np

# Constants
ROWS = 15
COLS = 15
LENGTH_FIELD_SIZE = 4


def create_msg(data):
    """
    Process: Create a valid protocol message, with length field
    :parameter: Data (str or any type that can be type casted to str)
    :return: Nothing
    """

    data = str(data)
    data_length = str(len(data))
    zfill_data_length = str(data_length.zfill(LENGTH_FIELD_SIZE))
    reply = zfill_data_length + data

    return reply.encode()


def get_msg(my_socket, time_out=None):
    """
    Process: Extract message from protocol, without the length field
    :parameter: My_socket (socket), time_out=None (can be in float or a None type)
    :return: If length field does not include a number or connecting is timed out, returns False, "Error".
    Otherwise return True, data
    """

    my_socket.settimeout(time_out)
    try:
        data_length = my_socket.recv(LENGTH_FIELD_SIZE).decode()
        if data_length.isnumeric():
            data = my_socket.recv(int(data_length)).decode()
            return True, data
        return False, "Error"
    except socket.timeout:
        return False, "Error"


def array_to_string(arr):
    """
    Process: parse numpy arr to string
    :parameter: Arr (numpy arr)
    :return: Arr parsed as str
    """

    return str(arr)


def string_to_array(str_arr):
    """
    Process: parse string to numpy arr
    :parameter: Str_arr (str)
    :return: Numpy arr from given string
    """

    # Removing unwanted characters and converting the string to a 1D array
    str_arr = str_arr.replace('[', '').replace(']', '').replace('\n', '')
    one_d_array = np.fromstring(str_arr, dtype=int, sep=' ')

    # Reshaping the 1D array into a 2D array
    rows, cols = ROWS, COLS
    two_d_array = one_d_array.reshape((rows, cols))
    return two_d_array
