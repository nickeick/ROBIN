import tkinter as tk

HEIGHT = 700
WIDTH = 800

def launch(pipe_conn):
    global pipe
    pipe = pipe_conn
    root.mainloop()

def test_functon(entry):
    label['text'] = "Entered: " + entry

root = tk.Tk()

canvas = tk.Canvas(root, height=HEIGHT, width=WIDTH)
canvas.pack()

#background_image = tk.PhotoImage(file='landscape.png')
#background_label = tk.Label(root, image=background_image)
#background_label.place(relwidth=1, relheight=1)

frame = tk.Frame(root, bg='yellow', bd=5)
frame.place(relx=0.5, rely=0.1, relwidth=0.75, relheight=0.1, anchor='n')

entry = tk.Entry(frame, font=40)
entry.place(relwidth=0.65, relheight=1)

button = tk.Button(frame, text="Test button", font=40, command=lambda: test_functon(entry.get()))
button.place(relx=0.7, relwidth=0.3, relheight=1)

lower_frame = tk.Frame(root, bg='yellow', bd=10)
lower_frame.place(relx=0.5, rely=0.25, relwidth=0.75, relheight=0.6, anchor='n')

label = tk.Label(lower_frame, bg='red', font=100)
label.place(relwidth=1, relheight=1)

list = tk.Listbox(lower_frame)
list.insert(1, "Python")
list.insert(2, "Java")
list.pack()

mb = tk.Menubutton(lower_frame, text="toppings")
mb.menu = tk.Menu(mb)
mb["menu"] = mb.menu

pepperoni = tk.IntVar()
pineapple = tk.IntVar()

mb.menu.add_checkbutton(label="pepperoni", variable=pepperoni)
mb.menu.add_checkbutton(label="pineapple", variable=pineapple)
mb.pack()

var = tk.StringVar()
message = tk.Message(lower_frame, textvariable=var)
var.set("Hello my friend")
message.pack()

var2 = tk.IntVar()
R1 = tk.Radiobutton(lower_frame, text="Number 1", variable=var2, value=1)
R1.pack()
R2 = tk.Radiobutton(lower_frame, text="Number 2", variable=var2, value=2)
R2.pack()
R3 = tk.Radiobutton(lower_frame, text="Number 3", variable=var2, value=3)
R3.pack()

var3 = tk.DoubleVar()
scale = tk.Scale(lower_frame, variable=var3)
scale.pack()

def start():
    pipe.send('launch')
    pipe.close()
    return

start_button = tk.Button(frame, text="Start ROBIN", command=start())
start_button.place(relx=0, rely=0, relwidth=0.5, relheight=0.5)
