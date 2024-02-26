import os
import shutil
if __name__ == "__main__":
    current_folder = os.path.dirname(os.path.abspath(__file__))
    for i in ["archives_to_be_sent","foto","Lakeshorefile","sorted","templates","uploadedfiles"]:
        if not os.path.exists(f"{current_folder}/{i}"):
            os.mkdir(f"{current_folder}/{i}")
    if os.path.exists(f"{current_folder}/main.html"):
        shutil.move(src=f"{current_folder}/main.html",dst=f"{current_folder}/templates/main.html")