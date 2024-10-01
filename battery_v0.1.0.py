### Liam Shaw
### 2/1/2024
###---------------------------------------------------------

import re, subprocess, customtkinter, rivalcfg, pystray, threading, time, webbrowser, json, os, sys, time, threading
import winreg as reg 
from plyer import notification
from PIL import Image

# Root settings
customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("dark-blue")
root = customtkinter.CTk()
root.title("Mouse Battery Program")
root.geometry ("400x200+1480+790")
root.resizable ("False","False")
root.overrideredirect(False)
# root.minsize (width=400, height=200)
# root.maxsize (width=800, height=400)

###---------------------------------------------------------
# Use a regular expression to find the battery percentage
ping_timer = None
next_trigger_time = None
message_timer = None
message_label = None
battery_amount = 0
battery_status = None
time_setting = 10
disconnected = 0

CONFIG_FILE = "battery_config.json"

def add_to_startup(app_name, app_path):
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = reg.OpenKey(reg.HKEY_CURRENT_USER, key_path, 0, reg.KEY_ALL_ACCESS)
        reg.SetValueEx(key, app_name, 0, reg.REG_SZ, app_path)
        reg.CloseKey(key)
        return True
    except WindowsError:
        return False

def remove_from_startup(app_name):
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = reg.OpenKey(reg.HKEY_CURRENT_USER, key_path, 0, reg.KEY_ALL_ACCESS)
        reg.DeleteValue(key, app_name)
        reg.CloseKey(key)
        return True
    except WindowsError:
        return False

def is_in_startup(app_name):
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = reg.OpenKey(reg.HKEY_CURRENT_USER, key_path, 0, reg.KEY_READ)
        reg.QueryValueEx(key, app_name)
        reg.CloseKey(key)
        return True
    except WindowsError:
        return False

def ping():
    global ping_timer, next_trigger_time, battery_amount, battery_status, disconnected
    console_output = subprocess.run(["rivalcfg", "--battery-level"], capture_output=True, text=True)
    battery_percentage = console_output.stdout
    print ("Ping!")

    status_search = re.search(r"Discharging|Charging", battery_percentage)
    if status_search:
        status = status_search.group()
        battery_status = status
        if status == "Discharging":
            charging_status_var.set ("Status: Draining")
        elif status == "Charging":
            charging_status_var.set ("Status: Charging")
        disconnected = 0
    else:
        charging_status_var.set ("Status: --")
        ping()
        disconnected += 1
        print(f"OH NO DISCONNECT!!!: {disconnected}")
        if disconnected >= 10:
            print("Device failed to connect.")
            return

    match = re.search(r"\d+", battery_percentage)
    if match:
        percentage = match.group()
        percentage_text_var.set("Battery: " + percentage + "%")
        battery_amount = (int(percentage))
        percentage = (int(percentage) / 100)
        progress_bar.set (percentage)
    else:
        percentage_text_var.set("Battery: --%")
        battery_amount = ("--")

    if ping_timer is not None:
        ping_timer.cancel()
    ping_timer = threading.Timer(time_setting, ping)
    ping_timer.daemon = True
    ping_timer.start()

     # Update the next trigger time
    next_trigger_time = time.time() + time_setting

###---------------------------------------------------------

is_shutting_down = False
def print_countdown():
    global next_trigger_time, is_shutting_down
    if is_shutting_down:
        return
    
    if next_trigger_time:
        # Calculate the time remaining until the next trigger
        time_left = int(next_trigger_time - time.time())
        button_text_var.set (f"Ping ({time_left}s)")
        if time_left <= 0:
            next_trigger_time = time.time() + time_setting  
    else:
        print("Timer not set yet.")

    countdown_timer = threading.Timer(1, print_countdown)
    countdown_timer.daemon = True
    countdown_timer.start()

###---------------------------------------------------------

# Mouse name label
mouse_name_var = customtkinter.StringVar()
mouse_name_label = customtkinter.CTkLabel(master=root,textvariable=mouse_name_var)
mouse_name_label.pack()

get_first_mouse = (str(rivalcfg.get_first_mouse()))

if get_first_mouse:
    mouse_name = re.sub(r"^<Mouse\s+","",get_first_mouse)
    mouse_name = re.sub(r"\s+\(\d+:\d+[a-zA-Z]?:\d+\)>$","",mouse_name)
    mouse_name_var.set (mouse_name)
else:
    mouse_name_var.set ("Unsupported Device")

###---------------------------------------------------------

# Charging or discharging label
charging_status_var = customtkinter.StringVar()
charging_status = customtkinter.CTkLabel(master=root,textvariable=charging_status_var)
charging_status.pack(padx=(100,0),anchor="w")

###---------------------------------------------------------

# Charging/discharging progress bar
progress_bar = customtkinter.CTkProgressBar(master=root,orientation="horizontal",height=30,progress_color="#099c05")
progress_bar.pack(fill="x",padx=30)
progress_bar.set (0)

###---------------------------------------------------------

# Percentage number label
percentage_text_var = customtkinter.StringVar()
percentage_display = customtkinter.CTkLabel(master=root,textvariable=percentage_text_var)
percentage_display.pack(padx=(100,0),anchor="w")

###---------------------------------------------------------

# Ping battery button
button_text_var = customtkinter.StringVar()
button = customtkinter.CTkButton(master=root,textvariable=button_text_var,command=lambda:ping())
button.pack(padx=10,anchor="s")

###---------------------------------------------------------

# Settings frame/behaviour initialization
def hide_settings():
    # Hide settings frame
    settings_frame.pack_forget()
    # Show main window content again
    show_main_content()

def save():
    print("SAVE!!!")
    
def show_frame(target_frame):
    for frame in [main_settings_frame, threshold_frame, dark_light_frame, notif_cooldown_frame, ping_cooldown_frame, auto_start_frame]:
        frame.pack_forget()
    target_frame.pack(fill="both", expand = True, padx = 5, pady = 5, anchor = "w")

# Settings main root frame and pages initialization
settings_frame = customtkinter.CTkFrame(master=root)
settings_frame.pack(fill="both", expand=True)
main_settings_frame = customtkinter.CTkFrame(master=settings_frame)
main_settings_label = customtkinter.CTkLabel(master=main_settings_frame, text="Thank you for downloading Rival Notifier!",font=("Arial", 12, "bold"))
main_settings_label.pack()
dark_light_frame = customtkinter.CTkFrame(master=settings_frame)
dark_light_label = customtkinter.CTkLabel(master=dark_light_frame,text="Dark/Light Mode Settings",font=("Arial", 12, "bold"))
dark_light_label.pack(pady=(5,0))
threshold_frame = customtkinter.CTkFrame(master=settings_frame)
threshold_label = customtkinter.CTkLabel(master=threshold_frame, text="Notification Threshold Settings",font=("Arial", 12, "bold"))
threshold_label.pack(pady=(5,0))
notif_cooldown_frame = customtkinter.CTkFrame(master=settings_frame)
notif_cooldown_label = customtkinter.CTkLabel(master=notif_cooldown_frame,text="Notification Cooldown Settings",font=("Arial", 12, "bold"))
notif_cooldown_label.pack(pady=(5,0))
ping_cooldown_frame = customtkinter.CTkFrame(master=settings_frame)
ping_cooldown_label = customtkinter.CTkLabel(master=ping_cooldown_frame,text="Ping Cooldown Settings",font=("Arial", 12, "bold"))
ping_cooldown_label.pack(pady=(5,0))
auto_start_frame = customtkinter.CTkFrame(master=settings_frame)
auto_start_label = customtkinter.CTkLabel(master=auto_start_frame,text="Auto Start Settings",font=("Arial", 12, "bold"))
auto_start_label.pack(pady=(5,0))

###---------------------------------------------------------

# Main settings elements
main_settings_label1 = customtkinter.CTkLabel(master=main_settings_frame, 
                                              text="This is my second try at software devlopment\nand I hope you benefit from it as I enjoyed making it :)",
                                              font=("Arial", 11))
main_settings_label1.pack(pady=(0,5))

img3 = Image.open('icons/1.png')
github_img = customtkinter.CTkImage(img3,size=(35,35))
github_label = customtkinter.CTkLabel(master=main_settings_frame,
                                              text="       Please report any issues or\n       suggestions to my github below!",
                                              font=("Arial",11),
                                              image=github_img,
                                              compound='left')
github_label.pack(padx=(15,0),anchor='w')

def open_github():
    gh_url = "https://github.com/cramslam"
    webbrowser.open_new_tab(gh_url)

github_button = customtkinter.CTkButton(master=main_settings_frame,
                                                text="github.com/cramslam",
                                                text_color="#7388ff",
                                                command=open_github,
                                                font=("Arial",11,"bold"),
                                                width=50,
                                                height=15,
                                                fg_color='transparent',
                                                hover_color= '#4d4d4d')
github_button.pack()

img2 = Image.open('icons/donate_icon_dark.png')
paypal_img = customtkinter.CTkImage(img2,size=(35,35))
paypal_label = customtkinter.CTkLabel(master=main_settings_frame,
                                              text="   If you enjoy the program and would like to\n   support me, feel free to visit my PayPal.me!",
                                              font=("Arial",11),
                                              image=paypal_img,
                                              compound='left')
paypal_label.pack(padx=(15,0),anchor='w')

def open_paypal():
    pp_url = "https://paypal.me/cramslam"
    webbrowser.open_new_tab(pp_url)

paypal_button = customtkinter.CTkButton(master=main_settings_frame,
                                                text="paypal.me/cramslam",
                                                text_color="#7388ff",
                                                command=open_paypal,
                                                font=("Arial",11,"bold"),
                                                width=50,
                                                height=15,
                                                fg_color='transparent',
                                                hover_color= '#4d4d4d')
paypal_button.pack()

show_again_checkbox = customtkinter.CTkCheckBox(master=main_settings_frame,
                                                text="Don't show again",
                                                font=("Arial",10,"bold"),
                                                text_color="#ababab",
                                                checkbox_height=10,
                                                checkbox_width=10,
                                                border_width=1)
show_again_checkbox.pack(padx=(0,15),anchor='e')

###---------------------------------------------------------

# Left side settings scrollable frame
settings_list_frame = customtkinter.CTkFrame(master=settings_frame)
settings_list_frame.pack(anchor = "e", side="left", fill="both", expand= False, padx=(5,0), pady=5)
settings_label = customtkinter.CTkLabel(master=settings_list_frame, text="Settings",font=("Arial", 13, "bold"))
settings_label.pack()
settings_scrollable = customtkinter.CTkScrollableFrame(master=settings_list_frame,fg_color='transparent')
settings_scrollable.configure(height=95,width=68)
settings_scrollable._scrollbar.configure(height=10,width=12)
settings_scrollable.pack()
close_button = customtkinter.CTkButton(master=settings_list_frame, text ="Close",command=hide_settings,width=80,height=20)
close_button.pack(padx=5,pady=5,side='bottom')
save_button = customtkinter.CTkButton(master=settings_list_frame, text ="Save",command=save,width=80,height=20)
save_button.pack(padx=5,side='bottom')

# Each button in the scrollable frame
auto_start_button = customtkinter.CTkButton(master=settings_scrollable,text="Auto Start",hover_color= '#4d4d4d',fg_color='#242424',font=("Arial", 10, "bold"),command=lambda:show_frame(auto_start_frame))
dark_light_button = customtkinter.CTkButton(master=settings_scrollable,text="Dark/Light\nMode",hover_color= '#4d4d4d',fg_color='#242424',font=("Arial", 10, "bold"),command=lambda:show_frame(dark_light_frame))
notif_thresh_button = customtkinter.CTkButton(master=settings_scrollable,text="Notification\nThreshold",hover_color= '#4d4d4d',fg_color='#242424',font=("Arial", 10, "bold"),command=lambda:show_frame(threshold_frame))
notif_cooldown_button = customtkinter.CTkButton(master=settings_scrollable,text="Notification\nCooldown",hover_color= '#4d4d4d',fg_color='#242424',font=("Arial", 10, "bold"),command=lambda:show_frame(notif_cooldown_frame))
ping_cooldown_button = customtkinter.CTkButton(master=settings_scrollable,text="Ping\nCooldown",hover_color= '#4d4d4d',fg_color='#242424',font=("Arial", 10, "bold"),command=lambda:show_frame(ping_cooldown_frame))
auto_start_button.pack(fill="y",pady=(0,3))
dark_light_button.pack(fill="y",pady=(0,3))
notif_thresh_button.pack(fill="y",pady=(0,3))
notif_cooldown_button.pack(fill="y",pady=(0,3))
ping_cooldown_button.pack(fill="y",pady=(0,3))


###---------------------------------------------------------



###---------------------------------------------------------
# Threshold selector behaviour initialization
checkbox_frame = customtkinter.CTkScrollableFrame(master=threshold_frame)
checkbox_frame.configure(height=60,width=70)
checkbox_frame.pack(side="right", expand= False, padx=5, pady=5)

def slider_event(value):
    value = (str(round(int((value * 100) + 0.01))) + ("%"))
    threshhold_label_var.set(value)

notif_threshhold = []
checkbox_list = []

def set_threshold(thresh_value, checkbox):
    global notif_threshhold
    if checkbox.get():
        if thresh_value not in notif_threshhold:
            notif_threshhold.append(thresh_value)
            notif_threshhold.sort()
    else:
        if thresh_value in notif_threshhold:
            notif_threshhold.remove(thresh_value)
    print(f"Updated notification thresholds: {notif_threshhold}")
    save_settings()  # Save settings after each change

def new_threshold():
    global notif_threshhold
    thresh_value = int(threshhold_label_var.get().replace("%", ""))
    
    if thresh_value not in notif_threshhold:
        notif_threshhold.append(thresh_value)
        notif_threshhold.sort()
        default_threshold()  # Refresh the checkboxes
        save_settings()  # Save settings after adding new threshold
    else:
        print(f"Threshold {thresh_value}% already exists!")

defaults_loaded = False
def default_threshold():
    global defaults_loaded, checkbox_list, notif_threshhold

    # Clear existing checkboxes
    for widget in checkbox_frame.winfo_children():
        widget.destroy()
    checkbox_list.clear()

    # Create checkboxes for all thresholds in notif_threshhold
    for thresh in notif_threshhold:
        checkbox = customtkinter.CTkCheckBox(
            master=checkbox_frame,
            text=f"{thresh}%",
            checkbox_height=20,
            checkbox_width=20
        )
        checkbox.pack(side='top', fill='x', padx=5, pady=5)
        checkbox.select()
        checkbox_list.append(thresh)
        
        # Set the command after the checkbox is created
        checkbox.configure(command=lambda value=thresh, cb=checkbox: set_threshold(value, cb))

    defaults_loaded = True

threshhold_label_var = customtkinter.StringVar()
threshhold_label_var.set("50%")
threshhold_label = customtkinter.CTkLabel(master=threshold_frame, textvariable = threshhold_label_var)
threshhold_label.pack(padx=(0,28))
threshold_slider = customtkinter.CTkSlider(master=threshold_frame, command= slider_event,number_of_steps=20,width=150 )
threshold_slider.pack(side='left',anchor='n',padx=5)
threshhold_button = customtkinter.CTkButton(master=threshold_frame, text="+", command=new_threshold, width=20, height=5)
threshhold_button.pack(side='left',anchor='n')

###---------------------------------------------------------

settings_frame.pack_forget()

def open_settings():
    if not show_again_checkbox.get():
        hide_main_content()
        show_frame(main_settings_frame)
    else:
        hide_main_content()
        show_frame(auto_start_frame)
    settings_frame.pack(fill="both", expand=True)

# Settings button
img1 = Image.open('icons/settings_icon_dark.png')
gear_image = customtkinter.CTkImage(img1)
settings_button = customtkinter.CTkButton(master=root,
                                          image=gear_image,
                                          text="",
                                          fg_color='transparent',
                                          width=10,
                                          command=open_settings)
settings_button.pack()
melabel = customtkinter.CTkLabel(master=root, text= "Version X.X.X - github.com/cramslam", font=("Arial", 10, "bold"))
melabel.pack()

# Settings window frame behaviour

def hide_main_content():
    # Hide main content, such as labels, buttons, etc.
    mouse_name_label.pack_forget()
    charging_status.pack_forget()
    progress_bar.pack_forget()
    percentage_display.pack_forget()
    button.pack_forget()
    settings_button.pack_forget()
    melabel.pack_forget()

def show_main_content():
    # Show main content again
    mouse_name_label.pack()
    charging_status.pack(padx=(100,0), anchor="w")
    progress_bar.pack(fill="x", padx=30)
    percentage_display.pack(padx=(100,0), anchor="w")
    button.pack(padx=10, anchor="s")
    settings_button.pack()
    melabel.pack()

###---------------------------------------------------------

# Return battery for notification use
return_battery_timer = None
def return_battery():
    global return_battery_timer, is_shutting_down, battery_status, battery_amount, notif_threshhold
    if is_shutting_down:
        return
    
    for thresh in notif_threshhold:
        if battery_status == 'Discharging' and battery_amount == thresh:
            print ("True")
            notification.notify(
            title = "Battery Low",
            message = f"Your battery is {battery_amount}%, consider plugging it in.",
            timeout = 10
        )
        else:
            print("False")
    


    print (battery_status, battery_amount)

    if return_battery_timer is not None:
        return_battery_timer.cancel()
    return_battery_timer = threading.Timer(time_setting, return_battery)
    return_battery_timer.daemon = True
    return_battery_timer.start()

###---------------------------------------------------------

# Autostart
def update_status_indicator(enabled):
    color = "#00FF00" if enabled else "#888888" 
    status_indicator.configure(fg_color=color)

def display_timed_message(message, color, duration=1500):
    global message_timer, message_label
    
    # Cancel any existing timer
    if message_timer:
        root.after_cancel(message_timer)
    
    # Update or create the message label
    if message_label:
        message_label.configure(text=message, text_color=color)
        message_label.pack(pady=5)
    else:
        message_label = customtkinter.CTkLabel(
            master=auto_start_frame,
            text=message,
            font=("Arial", 10),
            text_color=color,
            fg_color="transparent"
        )
        message_label.pack(pady=5)
    
    # Set a new timer to hide the message
    message_timer = root.after(duration, hide_message)

def hide_message():
    global message_label
    if message_label:
        message_label.pack_forget()

def toggle_auto_start():
    app_name = "Mouse Battery Notifier"
    if getattr(sys, 'frozen', False):
        app_path = sys.executable
    else:
        app_path = os.path.abspath(__file__)
    
    if auto_start_var.get():
        success = add_to_startup(app_name, app_path)
        message = "Auto-start enabled successfully"
        color = "green"
    else:
        success = remove_from_startup(app_name)
        message = "Auto-start disabled successfully"
        color = "red"
    
    if success:
        display_timed_message(message, color)
        update_status_indicator(auto_start_var.get())
    else:
        display_timed_message("Failed to update auto-start settings", "red")

# Update the auto-start UI elements
auto_start_frame = customtkinter.CTkFrame(master=settings_frame)
auto_start_label = customtkinter.CTkLabel(master=auto_start_frame, text="Auto Start Settings", font=("Arial", 12, "bold"))
auto_start_label.pack(pady=(5,0))

auto_start_container = customtkinter.CTkFrame(master=auto_start_frame, fg_color="transparent")
auto_start_container.pack(fill="x", padx=10, pady=5)

status_indicator = customtkinter.CTkLabel(
    master=auto_start_container,
    text="",
    font=("Arial", 1),
    text_color="#FFFFFF",
    fg_color="#888888",
    corner_radius=40,
    width=10,
    height=10
)
status_indicator.pack(side="left", padx=(0, 5))

auto_start_var = customtkinter.BooleanVar(value=is_in_startup("Mouse Battery Notifier"))
auto_start_switch = customtkinter.CTkSwitch(
    master=auto_start_container,
    text="Start on system startup",
    variable=auto_start_var,
    command=toggle_auto_start
)
auto_start_switch.pack(side="left")

# Initialize status indicator
update_status_indicator(auto_start_var.get())

###---------------------------------------------------------

def quit_window(icon, item):
    global ping_timer, return_battery_timer, is_shutting_down
    is_shutting_down = True

    if ping_timer is not None:
        ping_timer.cancel()

    if return_battery_timer is not None:
       return_battery_timer.cancel()
    
    save_settings()
    icon.stop()

    if root:
        root.destroy()

###---------------------------------------------------------

def show_window(icon, item):
    icon.stop()
    root.after(0,root.deiconify)

###---------------------------------------------------------

def hide_window():
    root.withdraw()
    image = Image.open('icons/icon4.ico')
    icon = pystray.Icon("Munchkin2", image, "Munchkin1", pystray.Menu(
        pystray.MenuItem("Open", show_window),
        pystray.MenuItem("Exit", quit_window),
    ))
    icon.run()

###---------------------------------------------------------

def save_settings():
    settings = {
        'auto_start': auto_start_var.get(),
        'notification_thresholds': notif_threshhold
    }
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(settings, f)
        print("Settings saved successfully.")
    except Exception as e:
        print(f"An error occurred while saving settings: {str(e)}")

def load_settings():
    global notif_threshhold
    try:
        if os.path.exists(CONFIG_FILE) and os.path.getsize(CONFIG_FILE) > 0:
            with open(CONFIG_FILE, 'r') as f:
                settings = json.load(f)
            auto_start_var.set(settings.get('auto_start', False))
            notif_threshhold = settings.get('notification_thresholds', [5, 10, 15, 25])
        else:
            # File doesn't exist or is empty, use default settings
            auto_start_var.set(False)
            notif_threshhold = [5, 10, 15, 25]
    except json.JSONDecodeError:
        print(f"Error reading {CONFIG_FILE}. Using default settings.")
        auto_start_var.set(False)
        notif_threshhold = [5, 10, 15, 25]
    except Exception as e:
        print(f"An error occurred while loading settings: {str(e)}")
        auto_start_var.set(False)
        notif_threshhold = [5, 10, 15, 25]

    # Update the auto-start status indicator
    update_status_indicator(auto_start_var.get())

    # Ensure the auto-start variable reflects the actual system state
    actual_auto_start_state = is_in_startup("Mouse Battery Notifier")
    if auto_start_var.get() != actual_auto_start_state:
        auto_start_var.set(actual_auto_start_state)
        update_status_indicator(actual_auto_start_state)
        print("Auto-start setting was out of sync with system state. Updated.")

    print(f"Settings loaded. \n- Auto-start is {'enabled' if auto_start_var.get() else 'disabled'}.")
    print(f"- Notification thresholds: {notif_threshhold}")

def initialize_thresholds():
    global notif_threshhold
    if not notif_threshhold:
        notif_threshhold = [5, 10, 15, 25]
    default_threshold()

###---------------------------------------------------------

print(f"Config file path: {os.path.abspath(CONFIG_FILE)}")

root.protocol('WM_DELETE_WINDOW', hide_window)

load_settings()
initialize_thresholds()
ping()
print_countdown()
return_battery()
root.mainloop()