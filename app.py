
import streamlit as st
import requests
import json
import base64
import uuid

# =====================================================
# 1. PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="Anjali's Kitchen",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# 2. WEBSITE DESIGN
# =====================================================

st.markdown("""
<style>

/* Main background */
.stApp {
    background-color: #ffffff;
    color: #292929;
}

/* Content width */
[data-testid="stMainBlockContainer"] {
    max-width: 1050px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* Typography */
h1, h2, h3 {
    color: #292929 !important;
    font-family: Georgia, serif !important;
    letter-spacing: -0.4px;
}

p {
    color: #555555;
    line-height: 1.65;
}

/* Header */
.main-title {
    text-align: center;
    font-family: Georgia, serif;
    font-size: 43px;
    font-weight: 600;
    color: #292929;
    margin-bottom: 5px;
}

.main-subtitle {
    text-align: center;
    color: #888888;
    font-size: 15px;
    margin-top: 0;
    margin-bottom: 25px;
}

/* Buttons */
.stButton > button,
.stFormSubmitButton > button {
    background-color: #292929;
    color: white;
    border: 1px solid #292929;
    border-radius: 7px;
    min-height: 42px;
    font-weight: 500;
    transition: 0.2s ease;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    background-color: #555555;
    color: white;
    border-color: #555555;
}

/* Input fields */
.stTextInput input,
.stTextArea textarea {
    border-radius: 7px;
    border: 1px solid #dddddd;
}

/* Select boxes */
.stSelectbox div[data-baseweb="select"] {
    border-radius: 7px;
}

/* Images */
[data-testid="stImage"] img {
    border-radius: 10px;
}

/* Dish cards */
[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid #eeeeee;
    border-radius: 12px;
    padding: 12px;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #fafafa;
}

/* Dividers */
hr {
    border-color: #eeeeee;
}

/* Captions */
.stCaption {
    color: #888888;
}

/* Footer */
.footer-text {
    text-align: center;
    color: #999999;
    font-size: 13px;
    padding-top: 20px;
}

/* Mobile adjustments */
@media (max-width: 640px) {
    .main-title {
        font-size: 32px;
    }

    [data-testid="stMainBlockContainer"] {
        padding-left: 1rem;
        padding-right: 1rem;
    }
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# 3. GITHUB CONFIGURATION
# =====================================================

OWNER = "iamssaroj"
REPO = "my-mothers-kitchen"
BRANCH = "main"
DATA_FILE = "data.json"
MAX_COMMENTS = 30

try:
    TOKEN = st.secrets["GITHUB_TOKEN"]
    ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

except Exception:
    st.error(
        "Website configuration is incomplete. "
        "Please configure GITHUB_TOKEN and ADMIN_PASSWORD "
        "in Streamlit Secrets."
    )
    st.stop()


API = f"https://api.github.com/repos/{OWNER}/{REPO}/contents"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}


# =====================================================
# 4. GITHUB STORAGE FUNCTIONS
# =====================================================

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

    content = base64.b64decode(
        result["content"]
    )

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

    data = json.loads(content.decode("utf-8"))

    if not isinstance(data, dict):
        raise ValueError("Invalid website data format.")

    if not isinstance(data.get("dishes"), list):
        data["dishes"] = []

    # Ensure every dish has a comments list
    for dish in data["dishes"]:
        if not isinstance(dish.get("comments"), list):
            dish["comments"] = []

    return data


def save_data(data):

    content = json.dumps(
        data,
        ensure_ascii=False,
        indent=2
    ).encode("utf-8")

    return save_file(
        DATA_FILE,
        content,
        "Update My Mother's Kitchen"
    )


# =====================================================
# 5. PHOTO UPLOAD FUNCTIONS
# =====================================================

def upload_photo(uploaded_file):

    extension = uploaded_file.name.rsplit(".", 1)[-1].lower()

    allowed_extensions = ["jpg", "jpeg", "png", "webp"]

    if extension not in allowed_extensions:
        raise ValueError(
            "Only JPG, JPEG, PNG and WEBP photos are allowed."
        )

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


# =====================================================
# 6. HEADER
# =====================================================

st.markdown(
    '<div class="main-title">Anjali\'s Kitchen</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="main-subtitle">'
    'Homemade flavours. Timeless recipes. Made with love.'
    '</div>',
    unsafe_allow_html=True
)

st.divider()


# =====================================================
# 7. LOAD WEBSITE DATA
# =====================================================

try:
    data = load_data()

except Exception as e:
    st.error(f"Unable to load website data: {e}")
    st.stop()


def count_comments(website_data):

    return sum(
        len(dish.get("comments", []))
        for dish in website_data["dishes"]
    )


total_comments = count_comments(data)


# =====================================================
# 8. NAVIGATION
# =====================================================

page = st.sidebar.radio(
    "Navigation",
    ["Home", "Admin"]
)


# =====================================================
# 9. HOME PAGE
# =====================================================

if page == "Home":

    st.markdown("## Our Homemade Dishes")

    st.caption(
        "Explore our dishes and share your experience."
    )

    if not data["dishes"]:

        st.info(
            "Our dishes will be displayed here soon. "
            "Please visit again!"
        )

    for dish in data["dishes"]:

        dish_comments = dish.get("comments", [])

        # ---------------- DISH CARD ----------------

        with st.container(border=True):

            image_col, details_col = st.columns(
                [1, 1.3],
                gap="large"
            )

            with image_col:

                if dish.get("photo"):

                    st.image(
                        photo_url(dish["photo"]),
                        use_container_width=True
                    )

                else:
                    st.info("Photograph unavailable.")

            with details_col:

                st.markdown(
                    f"### {dish.get('name', 'Untitled Dish')}"
                )

                description = dish.get(
                    "description",
                    ""
                )

                st.write(description)

                st.caption(
                    f"{len(dish_comments)} comments"
                )

            st.divider()

            # ---------------- COMMENTS ----------------

            st.markdown(
                f"**Customer Reviews ({len(dish_comments)})**"
            )

            if dish_comments:

                for comment in dish_comments:

                    with st.container(border=True):

                        rating = max(
                            1,
                            min(
                                5,
                                int(comment.get("rating", 5))
                            )
                        )

                        st.markdown(
                            f"**{comment.get('name', 'Guest')}** "
                            f"· {'⭐' * rating}"
                        )

                        st.write(
                            comment.get("text", "")
                        )

            else:

                st.caption(
                    "Be the first to share your experience!"
                )

            # ---------------- COMMENT FORM ----------------

            if total_comments < MAX_COMMENTS:

                with st.form(
                    f"comment_form_{dish['id']}",
                    clear_on_submit=True
                ):

                    st.markdown("**Share your experience**")

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

                    comment_text = st.text_area(
                        "Your comment",
                        placeholder="Write your experience here...",
                        key=f"text_{dish['id']}"
                    )

                    submitted = st.form_submit_button(
                        "Post Comment",
                        use_container_width=True
                    )

                    if submitted:

                        if not comment_text.strip():

                            st.warning(
                                "Please write a comment before submitting."
                            )

                        else:

                            try:
                                # Reload the latest data before saving
                                latest_data = load_data()

                                latest_total = count_comments(
                                    latest_data
                                )

                                if latest_total >= MAX_COMMENTS:

                                    st.warning(
                                        "The maximum limit of 30 comments "
                                        "has been reached."
                                    )

                                else:

                                    latest_dish = next(
                                        (
                                            d for d in latest_data["dishes"]
                                            if d["id"] == dish["id"]
                                        ),
                                        None
                                    )

                                    if latest_dish is None:

                                        st.error(
                                            "This dish is no longer available."
                                        )

                                    else:

                                        latest_dish.setdefault(
                                            "comments", []
                                        )

                                        latest_dish["comments"].append({
                                            "id": uuid.uuid4().hex,
                                            "name": name.strip() or "Guest",
                                            "rating": int(rating),
                                            "text": comment_text.strip()
                                        })

                                        save_data(latest_data)

                                        st.success(
                                            "Your comment has been published!"
                                        )

                                        st.rerun()

                            except Exception as e:

                                st.error(
                                    f"Could not publish comment: {e}"
                                )

            else:

                st.info(
                    "The maximum limit of 30 comments "
                    "has been reached."
                )

        st.write("")


# =====================================================
# 10. ADMIN PAGE
# =====================================================

elif page == "Admin":

    st.markdown("## Admin Panel")

    # ---------------- LOGIN ----------------

    if "admin_logged_in" not in st.session_state:

        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:

        st.markdown(
            "Login to manage dishes and customer comments."
        )

        with st.form("admin_login"):

            password = st.text_input(
                "Admin Password",
                type="password"
            )

            login_button = st.form_submit_button(
                "Login",
                use_container_width=True
            )

            if login_button:

                if password == ADMIN_PASSWORD:

                    st.session_state.admin_logged_in = True
                    st.rerun()

                else:

                    st.error("Incorrect password.")

    else:

        # ---------------- LOGOUT ----------------

        if st.button("Logout"):

            st.session_state.admin_logged_in = False
            st.rerun()

        st.success("Admin logged in successfully.")

        st.divider()

        # ---------------- SUMMARY ----------------

        st.markdown("### Website Summary")

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "Total Dishes",
                len(data["dishes"])
            )

        with col2:

            st.metric(
                "Total Comments",
                f"{total_comments}/{MAX_COMMENTS}"
            )

        st.divider()

        # =================================================
        # ADD NEW DISH
        # =================================================

        st.markdown("### Add New Dish")

        with st.form(
            "add_dish",
            clear_on_submit=True
        ):

            dish_name = st.text_input(
                "Dish Name"
            )

            description = st.text_area(
                "Dish Description"
            )

            photo = st.file_uploader(
                "Upload Dish Photograph",
                type=["jpg", "jpeg", "png", "webp"]
            )

            add_button = st.form_submit_button(
                "Add Dish",
                use_container_width=True
            )

            if add_button:

                if not dish_name.strip():

                    st.error("Dish name is required.")

                elif photo is None:

                    st.error(
                        "Please upload a dish photograph."
                    )

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

                        st.success(
                            "Dish added successfully!"
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"Unable to add dish: {e}"
                        )

        st.divider()

        # =================================================
        # EDIT AND DELETE DISHES
        # =================================================

        st.markdown("### Manage Dishes")

        if data["dishes"]:

            selected_id = st.selectbox(
                "Select Dish",
                options=[
                    dish["id"]
                    for dish in data["dishes"]
                ],
                format_func=lambda x: next(
                    dish["name"]
                    for dish in data["dishes"]
                    if dish["id"] == x
                )
            )

            selected_dish = next(
                dish
                for dish in data["dishes"]
                if dish["id"] == selected_id
            )

            if selected_dish.get("photo"):

                st.image(
                    photo_url(selected_dish["photo"]),
                    width=350
                )

            with st.form("edit_dish"):

                new_name = st.text_input(
                    "Dish Name",
                    value=selected_dish.get("name", "")
                )

                new_description = st.text_area(
                    "Dish Description",
                    value=selected_dish.get("description", "")
                )

                new_photo = st.file_uploader(
                    "Replace Photograph (optional)",
                    type=["jpg", "jpeg", "png", "webp"]
                )

                edit_button = st.form_submit_button(
                    "Save Changes",
                    use_container_width=True
                )

                if edit_button:

                    if not new_name.strip():

                        st.error(
                            "Dish name cannot be empty."
                        )

                    else:

                        try:

                            selected_dish["name"] = new_name.strip()

                            selected_dish["description"] = (
                                new_description.strip()
                            )

                            if new_photo is not None:

                                selected_dish["photo"] = upload_photo(
                                    new_photo
                                )

                            save_data(data)

                            st.success(
                                "Dish updated successfully!"
                            )

                            st.rerun()

                        except Exception as e:

                            st.error(
                                f"Update failed: {e}"
                            )

            st.write("")

            if st.button(
                "Delete This Dish",
                type="primary",
                use_container_width=True
            ):

                data["dishes"] = [
                    dish
                    for dish in data["dishes"]
                    if dish["id"] != selected_id
                ]

                try:

                    save_data(data)

                    st.success(
                        "Dish and its comments deleted."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Deletion failed: {e}"
                    )

        else:

            st.info(
                "No dishes have been added yet."
            )

        st.divider()

        # =================================================
        # MANAGE COMMENTS
        # =================================================

        st.markdown("### Manage Comments")

        comment_items = []

        for dish in data["dishes"]:

            for comment in dish.get("comments", []):

                comment_items.append({
                    "dish_id": dish["id"],
                    "comment_id": comment["id"],
                    "dish_name": dish["name"],
                    "comment_name": comment.get("name", "Guest"),
                    "comment_text": comment.get("text", "")
                })

        if comment_items:

            selected_comment = st.selectbox(
                "Select Comment",
                options=range(len(comment_items)),
                format_func=lambda i: (
                    f"{comment_items[i]['comment_name']} — "
                    f"{comment_items[i]['dish_name']}: "
                    f"{comment_items[i]['comment_text'][:45]}"
                )
            )

            selected_item = comment_items[selected_comment]

            st.markdown("**Selected Comment**")

            st.write(
                selected_item["comment_text"]
            )

            if st.button(
                "Delete Selected Comment",
                use_container_width=True
            ):

                for dish in data["dishes"]:

                    if dish["id"] == selected_item["dish_id"]:

                        dish["comments"] = [
                            comment
                            for comment in dish.get("comments", [])
                            if comment["id"] != selected_item["comment_id"]
                        ]

                try:

                    save_data(data)

                    st.success(
                        "Comment deleted successfully."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Deletion failed: {e}"
                    )

        else:

            st.caption(
                "No comments available."
            )


# =====================================================
# 11. FOOTER
# =====================================================

st.divider()

st.markdown(
    '<div class="footer-text">'
    'Anjali\'s Kitchen · Homemade with love ❤️ · By Santosh'
    '</div>',
    unsafe_allow_html=True
)
