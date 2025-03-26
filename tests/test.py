import requests


base_url = "http://localhost:5000"


def create_contest(n, a, st,et):
    d ={
        "name":n,
        "admin_id":a,
        "start_datetime":st ,
        "end_datetime":st
    }
    return requests.post(base_url+"/contests", json=d).json()


def get_contests():
    return requests.get(base_url+"/contests").json()


def add_partecipant_to_contest(ci, n):
    d ={
        "username":n
    }
    return requests.post(base_url+f"/contests/{ci}/add_new_partecipant", json=d).json()


print(create_contest("test", 1, "2025-05-06 00:00:00", "2025-05-07 00:00:00"))
print(get_contests())
print(add_partecipant_to_contest(1, "vrv@gmail.com"))
print(get_contests())