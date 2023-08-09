# python -m venv venv
# on windows
#   venv\Scripts\activate
# on macos/linux
#   source venv/bin/activate
# python -m pip install google-api-python-client google-auth google-auth-httplib2 google-auth-oauthlib tk

import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from datetime import datetime
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build

# vars
search_var = None
table = None
search_results = []
current_result_index = -1
root = tk.Tk()

def get_authenticated_service():
    # Load the credentials from the client secrets JSON file
    credentials = None
    if os.path.exists('credentials.json'):
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            'credentials.json',
            scopes=['https://www.googleapis.com/auth/youtube.readonly']
        )
        credentials = flow.run_local_server()

    # Return an authenticated YouTube Data API service
    return build('youtube', 'v3', credentials=credentials)

def get_subscribed_channels(youtube):
    subscribed_channels = []
    next_page_token = None

    while True:
        # Get the list of subscribed channels with a page token
        subscriptions = youtube.subscriptions().list(
            part='snippet',
            mine=True,
            maxResults=50,  # Adjust this value based on your preference
            pageToken=next_page_token
        ).execute()

        subscribed_channels.extend(subscriptions.get('items', []))

        next_page_token = subscriptions.get('nextPageToken')
        if not next_page_token:
            break

    return subscribed_channels


def display_subscribed_channels_gui(subscribed_channels):
    root.title("Subscribed Channels")

    global search_var
    search_var = tk.StringVar()

    search_frame = ttk.Frame(root)
    search_frame.pack(pady=10)

    search_entry = ttk.Entry(search_frame, textvariable=search_var)
    search_entry.pack(side="left", expand=True, padx=5)

    search_button = ttk.Button(search_frame, text="Search", command=filter_channels, style="Sharp.TButton")
    search_button.pack(side="left", expand=True,padx=5)

    prev_button = ttk.Button(search_frame, text="<<", command=select_previous_result, style="Sharp.TButton")
    prev_button.pack(side="left", padx=5)

    next_button = ttk.Button(search_frame, text=">>", command=select_next_result, style="Sharp.TButton")
    next_button.pack(side="left", padx=5)

    global table
    table = ttk.Treeview(root, columns=("date_subscribed", "time_since_subscribed", "channel_name", "channel_link"), show="headings")
    table.heading("date_subscribed", text="Date Subscribed")
    table.heading("time_since_subscribed", text="Time Since Subscribed")
    table.heading("channel_name", text="Channel Name")
    table.heading("channel_link", text="Channel Link")

    scrollbar = ttk.Scrollbar(root, orient="vertical", command=table.yview)
    table.configure(yscrollcommand=scrollbar.set)

    table.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    for channel in subscribed_channels:
        channel_id = channel['snippet']['resourceId']['channelId']
        channel_name = channel['snippet']['title']
        subscribed_at = channel['snippet']['publishedAt']
        channel_link = f"https://www.youtube.com/channel/{channel_id}"
        time_since_subscribed = calculate_time_since_subscribed(subscribed_at)

        table.insert("", "end", values=(subscribed_at[:10], time_since_subscribed, channel_name, channel_link))

    root.mainloop()


def calculate_time_since_subscribed(subscribed_at):
    try:
        # Try parsing with milliseconds format
        subscribed_date = datetime.strptime(subscribed_at, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        try:
            # If parsing with milliseconds format fails, try without milliseconds
            subscribed_date = datetime.strptime(subscribed_at, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            raise ValueError(f"Unable to parse subscribed_at: {subscribed_at}")

    # Get the current date
    current_date = datetime.now()

    # Calculate the time difference
    time_since_subscribed = current_date - subscribed_date

    # Calculate the years, months, and days
    years = time_since_subscribed.days // 365
    months = (time_since_subscribed.days % 365) // 30
    days = time_since_subscribed.days % 30

    # Construct the result string
    result = f"{years}y, {months}m, {days}d"
    return result

def filter_channels():
    global search_results
    global current_result_index
    search_text = search_var.get().lower()
    search_results = []
    current_result_index = -1
    for row in table.get_children():
        if search_text in table.item(row)['values'][2].lower():
            search_results.append(row)
    if len(search_results) > 0:
        current_result_index = 0
        table.selection_set(search_results[0])
        table.focus(search_results[0])
        table.see(search_results[0])
        update_prev_next_buttons()
    else:
        table.selection_clear()
        update_prev_next_buttons()

def create_styles():
    ttk.Style().configure("Sharp.TButton", relief="flat", borderwidth=0)

    ttk.Style().configure("Light.Treeview", background="#FFFFFF", foreground="#000000")
    ttk.Style().map("Light.Treeview", background=[("selected", "#D3D3D3")])

    ttk.Style().configure("Dark.Treeview", background="#222222", foreground="#FFFFFF")
    ttk.Style().map("Dark.Treeview", background=[("selected", "#555555")])

def select_previous_result():
    global current_result_index
    current_result_index -= 1
    if current_result_index < 0:
        current_result_index = len(search_results) - 1
    table.selection_set(search_results[current_result_index])
    table.focus(search_results[current_result_index])
    table.see(search_results[current_result_index])
    update_prev_next_buttons()

def select_next_result():
    global current_result_index
    current_result_index += 1
    if current_result_index >= len(search_results):
        current_result_index = 0
    table.selection_set(search_results[current_result_index])
    table.focus(search_results[current_result_index])
    table.see(search_results[current_result_index])
    update_prev_next_buttons()

def update_prev_next_buttons():
    global search_results
    global current_result_index

if __name__ == '__main__':
    youtube = get_authenticated_service()
    subscribed_channels = get_subscribed_channels(youtube)
    # Sort channels by subscription date (oldest to newest)
    subscribed_channels.sort(key=lambda channel: channel['snippet']['publishedAt'])
    display_subscribed_channels_gui(subscribed_channels)