import ipaddress, subprocess, time
from tkinter import *
from tkinter import filedialog, messagebox
from receiver import Receiver
from threading import Thread
from constants import UDP_SCHEME, LOCAL_HOST, SRT_SCHEME

INTERNAL_PORT = 5000


def on_close_window():
    global continue_polling
    continue_polling = False
    global continue_receiving
    continue_receiving = False
    root.destroy()


def poll():
    global continue_polling
    continue_polling = True
    while continue_polling:
        time.sleep(5)
        receiver.get_streams()


def receive():
    global continue_receiving
    continue_receiving = True
    while continue_receiving:
        check_status()
        stream_id, ip, port, is_rendezvous = receiver.consume_stream()
        if ip and port:
            if is_rendezvous:
                receiver.processes[stream_id] = [
                    subprocess.Popen(
                        [
                            "srt-live-transmit",
                            f"{SRT_SCHEME}://{ip}:{port}?mode=rendezvous",
                            f"{UDP_SCHEME}://{LOCAL_HOST}:{INTERNAL_PORT}",
                        ]
                    )
                ]
                receiver.processes[stream_id].insert(
                    0,
                    subprocess.Popen(
                        [
                            "ffplay",
                            "-v",
                            "fatal",
                            f"{UDP_SCHEME}://{LOCAL_HOST}:{INTERNAL_PORT}",
                        ]
                    ),
                )
                INTERNAL_PORT += 1
            else:
                receiver.processes[stream_id] = [
                    subprocess.Popen(
                        [
                            "ffplay",
                            "-v",
                            "fatal",
                            f"{SRT_SCHEME}://{ip}:{port}?mode=listener",
                        ]
                    )
                ]


def check_status():
    stream_ids = list(receiver.processes.keys())
    for stream_id in stream_ids:
        # First, check if stream has been manually closed
        if receiver.processes[stream_id][0].poll() is not None:
            for process in receiver.processes[stream_id]:
                process.terminate()
            del receiver.processes[stream_id]
            receiver.delete_stream(stream_id)
        else:
            stream_deleted = True
            for stream in receiver.streams:
                if stream["id"] == int(stream_id):
                    stream_deleted = False
            if stream_deleted:
                for process in receiver.processes[stream_id]:
                    process.terminate()
                del receiver.processes[stream_id]


def register():
    receiver.display_name = display_name_entry.get()
    receiver.serial_number = serial_number_entry.get()
    channel_1_port = channel_1_port_entry.get()
    channel_2_port = channel_2_port_entry.get()
    if not is_valid_port(channel_1_port) or not is_valid_port(channel_2_port):
        messagebox.showerror("Error", "Invalid port.")
        return
    else:
        receiver.channel_1_port = channel_1_port
        receiver.channel_2_port = channel_2_port
    return_message = receiver.register()
    if return_message == "Decoder already registered!":
        messagebox.showerror("Error", return_message)
    else:
        messagebox.showinfo("Info", return_message)


def start():
    Thread(target=poll).start()
    Thread(target=receive).start()


def is_valid_ip(ip):
    if ip == "localhost":
        return True
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return False
    return True


def is_valid_port(port):
    try:
        port = int(port)
        if port >= 1 and port <= 65535:
            return True
        else:
            return False
    except ValueError:
        return False


root = Tk()
root.title("Switchboard - Sample Receiver")
root.geometry("800x400")
root.iconphoto(True, PhotoImage(file=r"public/bean.png"))
receiver = Receiver()
default_font = ("TkDefaultFont", 12)

# Registration section elements
registration_label_frame = LabelFrame(root, text="Registration", font=default_font, borderwidth=4)
display_name_label = Label(
    registration_label_frame, text="Display Name", font=default_font, width=20
)
display_name_entry = Entry(registration_label_frame, width=30, font=default_font)
display_name_entry.insert(0, receiver.display_name)
serial_number_label = Label(
    registration_label_frame, text="Serial Number", font=default_font, width=20
)
serial_number_entry = Entry(registration_label_frame, width=30, font=default_font)
serial_number_entry.insert(0, receiver.serial_number)
channel_1_port_label = Label(
    registration_label_frame, text="Channel 1 Port", width=20, font=default_font
)
channel_1_port_entry = Entry(registration_label_frame, width=30, font=default_font)
channel_1_port_entry.insert(0, receiver.channel_1_port)
channel_2_port_label = Label(
    registration_label_frame, text="Channel 2 Port", width=20, font=default_font
)
channel_2_port_entry = Entry(registration_label_frame, width=30, font=default_font)
channel_2_port_entry.insert(0, receiver.channel_2_port)
register_button = Button(
    registration_label_frame,
    text="Register",
    font=default_font,
    bg="#57A834",
    width=20,
    command=register,
)

# Listening Instructions section elements
listening_label_frame = LabelFrame(root, font=default_font, borderwidth=4)
start_button = Button(
    listening_label_frame,
    text="Start",
    font=default_font,
    bg="#57A834",
    width=20,
    command=start,
)

# Placing on grid
registration_label_frame.pack(expand="yes", fill="both")
display_name_label.grid(row=0, column=0)
display_name_entry.grid(row=0, column=1, pady=10)
serial_number_label.grid(row=1, column=0)
serial_number_entry.grid(row=1, column=1)
channel_1_port_label.grid(row=2, column=0)
channel_1_port_entry.grid(row=2, column=1, pady=10)
channel_2_port_label.grid(row=3, column=0)
channel_2_port_entry.grid(row=3, column=1)
register_button.grid(row=0, column=2, rowspan=2, padx=20, pady=5)
listening_label_frame.pack(expand="yes", fill="both")
start_button.place(relx=0.5, rely=0.5, anchor=CENTER)

root.protocol("WM_DELETE_WINDOW", on_close_window)
root.mainloop()