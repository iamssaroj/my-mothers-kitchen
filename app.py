
import streamlit as st
import requests
import json
import base64
import uuid

# ---------------- CONFIGURATION ----------------

st.set_page_config(
    page_title="My Mother's Kitchen",
    page_icon="🍲",
    layout="wide"
)

OWNER = "iamssaroj"
REPO = "my-mothers-kitchen"
BRANCH = "main"
DATA_FILE = "data.json"

try:
    TOKEN = st.secrets["GITHUB_TOKEN"]
    ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
except Exception:
    st.error("Website configuration is incomplete. Please configure Streamlit secrets.")
    st.stop()

API = f"https://api.github.com/repos/{OWNER}/{REPO}/contents"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}


# ---------------- GITHUB STORAGE ----------------

def get_file(path):
    response = requests.get(
        f"{API}/{path}",
        headers=HEADERS,
        params={"ref": BRANCH},
        timeout=20
    )

    if response.status_code == 404:
        return None, None

    response.raise_for_status()

    result = response.json()
    content = base64.b64decode(result["content"]).decode("utf-8")

    return content, result["sha"]


def save_file(path, content, message):
    _, sha = get_file(path)

    payload = {
        "message": message,
        "content": base64.b64encode(content).decode("utf-8"),
        "branch": BRANCH
    }

    if sha:
        payload["sha"] = sha

    response = requests.put(
        f"{API}/{path}",
        headers=HEADERS,
        json=payload,
        timeout=30
    )

    response.raise_for_status()
    return True


def load_data():
    content, _ = get_file(DATA_FILE)

    if content is None:
        return {"dishes": []}

    return json.loads(content)


def save_data(data):
    content = json.dumps(
        data,
        ensure_ascii=False,
        indent=2
    ).encode("utf-8")

    return save_file(
        DATA_FILE,
        content,
        "Update kitchen website data"
    )


def upload_photo(uploaded_file):
    extension = uploaded_file.name.rsplit(".", 1)[-1].lower()

    if extension not in ["jpg", "jpeg", "png", "webp"]:
        raise ValueError("Only JPG, JPEG, PNG and WEBP photos are allowed.")

    filename = f"images/{uuid.uuid4().hex}.{extension}"

    save_file(
        filename,
        uploaded_file.getvalue(),
        "Upload dish photograph"
    )

    return filename


def photo_url(path):
    return (
        f"https://raw.githubusercontent.com/"
        f"{OWNER}/{REPO}/{BRANCH}/{path}"
    )


# ---------------- HEADER ----------------

st.title("🍲 My Mother's Kitchen")
st.markdown(
    "### Homemade food, prepared with love ❤️"
)
st.caption("Discover our dishes and share your experience.")

st.divider()

try:
    data = load_data()
except Exception as e:
    st.error(f"Unable to load website data: {e}")
    st.stop()

total_comments = sum(
    len(dish.get("comments", []))
    for dish in data["dishes"]
)


# ---------------- NAVIGATION ----------------

page = st.sidebar.radio(
    "Navigation",
    ["Home", "Admin"]
)


# ---------------- HOME PAGE ----------------

if page == "Home":

    st.header("Our Homemade Dishes")

    if not data["dishes"]:
        st.info("Our dishes will be displayed here soon.")

    for dish in data["dishes"]:

        st.subheader(dish["name"])

        if dish.get("photo"):
            st.image(
                photo_url(dish["photo"]),
                use_container_width=True
            )

        st.write(dish.get("description", ""))

        comments = dish.get("comments", [])

        st.markdown(f"**Comments ({len(comments)})**")

        if comments:
            for comment in comments:
                with st.container(border=True):
                    st.markdown(
                        f"**{comment['name']}** "
                        f"· {'⭐' * comment['rating']}"
                    )
                    st.write(comment["text"])
        else:
            st.caption("Be the first to share your experience!")

        if total_comments < 30:

            with st.form(f"comment_{dish['id']}"):

                st.markdown("**Write a comment**")

                name = st.text_input(
                    "Your name (optional)",
                    key=f"name_{dish['id']}"
                )

                rating = st.select_slider(
                    "Your rating",
                    options=[1, 2, 3, 4, 5],
                    value=5,
                    key=f"rating_{dish['id']}"
                )

                text = st.text_area(
                    "Your comment",
                    key=f"text_{dish['id']}"
                )

                submitted = st.form_submit_button(
                    "Post Comment",
                    use_container_width=True
                )

                if submitted:

                    if not text.strip():
                        st.warning("Please write a comment.")

                    elif total_comments >= 30:
                        st.warning("Maximum 30 comments reached.")

                    else:
                        dish["comments"].append({
                            "id": uuid.uuid4().hex,
                            "name": name.strip() or "Guest",
                            "rating": int(rating),
                            "text": text.strip()
                        })

                        try:
                            save_data(data)
                            st.success("Your comment has been published!")
                            st.rerun()
                        except Exception as e:
                            dish["comments"].pop()
                            st.error(f"Could not publish comment: {e}")

        else:
            st.info("The maximum limit of 30 comments has been reached.")

        st.divider()


# ---------------- ADMIN PAGE ----------------

elif page == "Admin":

    st.header("Admin Panel")

    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:

        password = st.text_input(
            "Admin Password",
            type="password"
        )

        if st.button("Login"):

            if password == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("Incorrect password.")

    else:

        if st.button("Logout"):
            st.session_state.admin_logged_in = False
            st.rerun()

        st.success("Admin logged in successfully.")

        st.write(f"Total dishes: {len(data['dishes'])}")
        st.write(f"Comments received: {total_comments}/30")

        # ADD DISH

        st.subheader("Add New Dish")

        with st.form("add_dish", clear_on_submit=True):

            dish_name = st.text_input("Dish Name")
            description = st.text_area("Dish Description")

            photo = st.file_uploader(
                "Upload Dish Photograph",
                type=["jpg", "jpeg", "png", "webp"]
            )

            add_button = st.form_submit_button("Add Dish")

            if add_button:

                if not dish_name.strip():
                    st.error("Dish name is required.")

                elif photo is None:
                    st.error("Please upload a dish photograph.")

                else:
                    try:
                        photo_path = upload_photo(photo)

                        data["dishes"].append({
                            "id": uuid.uuid4().hex,
                            "name": dish_name.strip(),
                            "description": description.strip(),
                            "photo": photo_path,
                            "comments": []
                        })

                        save_data(data)
                        st.success("Dish added successfully!")
                        st.rerun()

                    except Exception as e:
                        st.error(f"Unable to add dish: {e}")

        st.divider()

        # EDIT AND DELETE DISH

        st.subheader("Manage Dishes")

        if data["dishes"]:

            selected_id = st.selectbox(
                "Select Dish",
                options=[d["id"] for d in data["dishes"]],
                format_func=lambda x: next(
                    d["name"] for d in data["dishes"]
                    if d["id"] == x
                )
            )

            selected_dish = next(
                d for d in data["dishes"]
                if d["id"] == selected_id
            )

            with st.form("edit_dish"):

                new_name = st.text_input(
                    "Dish Name",
                    value=selected_dish["name"]
                )

                new_description = st.text_area(
                    "Description",
                    value=selected_dish["description"]
                )

                new_photo = st.file_uploader(
                    "Replace Photograph (optional)",
                    type=["jpg", "jpeg", "png", "webp"]
                )

                edit_button = st.form_submit_button("Save Changes")

                if edit_button:

                    try:
                        if not new_name.strip():
                            st.error("Dish name cannot be empty.")
                        else:
                            selected_dish["name"] = new_name.strip()
                            selected_dish["description"] = new_description.strip()

                            if new_photo is not None:
                                selected_dish["photo"] = upload_photo(new_photo)

                            save_data(data)
                            st.success("Dish updated!")
                            st.rerun()

                    except Exception as e:
                        st.error(f"Update failed: {e}")

            if st.button("Delete This Dish", type="primary"):

                data["dishes"] = [
                    d for d in data["dishes"]
                    if d["id"] != selected_id
                ]

                try:
                    save_data(data)
                    st.success("Dish and its comments deleted.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Deletion failed: {e}")

        else:
            st.info("No dishes have been added yet.")

        st.divider()

        # DELETE COMMENTS

        st.subheader("Manage Comments")

        comment_items = []

        for dish in data["dishes"]:
            for comment in dish.get("comments", []):
                comment_items.append(
                    (dish["id"], comment["id"], dish["name"],
                     comment["name"], comment["text"])
                )

        if comment_items:

            selected_comment = st.selectbox(
                "Select comment to delete",
                options=range(len(comment_items)),
                format_func=lambda i: (
                    f"{comment_items[i][3]} — "
                    f"{comment_items[i][2]}: "
                    f"{comment_items[i][4][:45]}"
                )
            )

            if st.button("Delete Selected Comment"):

                dish_id, comment_id = (
                    comment_items[selected_comment][0],
                    comment_items[selected_comment][1]
                )

                for dish in data["dishes"]:
                    if dish["id"] == dish_id:
                        dish["comments"] = [
                            c for c in dish["comments"]
                            if c["id"] != comment_id
                        ]

                try:
                    save_data(data)
                    st.success("Comment deleted.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Deletion failed: {e}")

        else:
            st.caption("No comments available.")
