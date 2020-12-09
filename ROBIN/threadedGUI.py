from tkinter import Button, Frame, Canvas, Tk
from threading import Thread
from queue import Queue


class GuiPart:
    def __init__(self, master, queue):
        self.master = master
        self.queue = queue
        # Set up the GUI
        canvas = Canvas(master, height=300, width=400)
        canvas.pack()

        frame = Frame(master, bg='yellow', bd=5)
        frame.place(relx=0.5, rely=0.1, relwidth=0.75, relheight=0.75, anchor='n')

        console = Button(frame, text='Start ROBIN', command=self.start_robin)
        console.pack(side = 'left', padx=5, pady=5, anchor='n')

        console = Button(frame, text='Close', command=self.exit)
        console.pack(side = 'right', padx=1, pady=1, anchor='n')

        console = Button(frame, text='Shutdown', command=self.shutdown)
        console.place(relx=0.5, rely = 0.9, anchor='s')

    def start_robin(self):
        self.queue.put('hello Robin')

    def get_time(self):
        self.queue.put('time')

    def exit(self):
        self.master.destroy()

    def shutdown(self):
        self.queue.put('goodbye')
        self.queue.put('exit')
        self.exit()
        # Add more GUI stuff here depending on your specific needs


class ThreadedClient:
    def __init__(self, master, queue, worker1, worker2=None):
        self.master = master

        # Set up the GUI part
        self.gui = GuiPart(master, queue)

        # Set up the thread to do asynchronous I/O
        # More threads can also be created and used, if necessary
        self.thread1 = Thread(target=worker1)
        self.thread1.start()

        # self.thread2 = threading.Thread(target=worker2)
        # self.thread2.start()



if __name__ == '__main__':
    root = Tk()

    client = ThreadedClient(root, queue)
    root.mainloop()

#initialize()
