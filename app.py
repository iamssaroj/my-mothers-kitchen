
import streamlit as st
import requests
import json
import base64
import uuid
import html

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
# 2. DESIGN AND STYLING
# =====================================================

st.markdown("""
<style>

.stApp {
    background: #ffffff;
    color: #292929;
}

[data-testid="stMainBlockContainer"] {
    max-width: 1120px;
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}

h1, h2, h3 {
    font-family: Georgia, serif !important;
    color: #292929 !important;
}

p {
    color: #626262;
    line-height: 1.7;
}

/* Website header */

.site-title {
    text-align: center;
    font-family: Georgia, serif;
    font-size: 43px;
    font-weight: 600;
    color: #292929;
    margin-bottom: 4px;
}

.site-tagline {
    text-align: center;
    color: #898989;
    font-size: 14px;
    letter-spacing: 1px;
    margin-bottom: 24px;
}

/* Hero section */

.hero-label {
    color: #A47745;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 2px;
    margin-bottom: 12px;
}

.hero-heading {
    font-family: Georgia, serif;
    font-size: 43px;
    line-height: 1.2;
    font-weight: 600;
    color: #292929;
    margin-bottom: 16px;
}

.hero-description {
    font-size: 16px;
    color: #727272;
    line-height: 1.9;
}

.hero-note {
    color: #A47745;
    font-family: Georgia, serif;
    font-size: 17px;
    font-style: italic;
    margin-top: 18px;
}

/* Section headings */

.section-label {
    color: #A47745;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    margin-bottom: 5px;
}

.section-heading {
    font-family: Georgia, serif;
    font-size: 31px;
    color: #292929;
    margin-bottom: 5px;
}

/* Images */

[data-testid="stImage"] img {
    border-radius: 12px;
}

/* Buttons */

.stButton > button,
.stFormSubmitButton > button {
    background: #292929;
    color: white;
    border: 1px solid #292929;
    border-radius: 7px;
    min-height: 42px;
    font-weight: 500;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    background: #555555;
    color: white;
    border-color: #555555;
}

/* Inputs */

.stTextInput input,
.stTextArea textarea {
    border-radius: 7px;
    border: 1px solid #dddddd;
}

.stSelectbox div[data-baseweb="select"] {
    border-radius: 7px;
}

/* Sidebar */

[data-testid="stSidebar"] {
    background: #faf9f7;
}

/* Dividers */

hr {
    border-color: #eeeeee;
}

/* Footer */

.site-footer {
    text-align: center;
    color: #999999;
    font-size: 13px;
    padding: 18px 0;
}

/* Mobile */

@media (max-width: 640px) {
    .site-title {
        font-size: 33px;
    }

    .hero-heading {
        font-size: 33px;
    }

    .section-heading {
        font-size: 26px;
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
    st.error("Please configure your Streamlit Secrets.")
    st.stop()

API = f"https://api.github.com/repos/{OWNER}/{REPO}/contents"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}


# =====================================================
# 4. GITHUB STORAGE
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

    content = base64.b64decode(result["content"])

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
        raise ValueError("Invalid data.json format.")

    if not isinstance(data.get("dishes"), list):
        data["dishes"] = []

    for dish in data["dishes"]:
        dish.setdefault("comments", [])

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
        "Update Anjali's Kitchen"
    )


def count_comments(data):

    return sum(
        len(dish.get("comments", []))
        for dish in data["dishes"]
    )


# =====================================================
# 5. PHOTO FUNCTIONS
# =====================================================

def upload_photo(uploaded_file):

    extension = uploaded_file.name.rsplit(".", 1)[-1].lower()

    if extension not in ["jpg", "jpeg", "png", "webp"]:
        raise ValueError("Invalid image format.")

    filename = f"images/{uuid.uuid4().hex}.{extension}"

    save_file(
        filename,
        uploaded_file.getvalue(),
        "Upload food photograph"
    )

    return filename


def photo_url(path):

    return (
        f"https://raw.githubusercontent.com/"
        f"{OWNER}/{REPO}/{BRANCH}/{path}"
    )


# =====================================================
# 6. LOAD WEBSITE DATA
# =====================================================

try:
    data = load_data()

except Exception as e:
    st.error(f"Unable to load website data: {e}")
    st.stop()

total_comments = count_comments(data)


# =====================================================
# 7. WEBSITE HEADER
# =====================================================

st.markdown(
    '<div class="site-title">Anjali\'s Kitchen</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="site-tagline">'
    'HOMEMADE FLAVOURS · TRADITIONAL RECIPES · MADE WITH LOVE'
    '</div>',
    unsafe_allow_html=True
)

st.divider()


# =====================================================
# 8. NAVIGATION
# =====================================================

page = st.sidebar.radio(
    "Explore",
    ["Home", "Admin"]
)


# =====================================================
# 9. HOME PAGE
# =====================================================

if page == "Home":

    # ---------------- HERO SECTION ----------------

    hero_left, hero_right = st.columns(
        [1.1, 1],
        gap="large",
        vertical_alignment="center"
    )

    with hero_left:

        st.markdown(
            """
            <div class="hero-label">
                WELCOME TO ANJALI'S KITCHEN
            </div>

            <div class="hero-heading">
                A little taste of home,
                in every bite.
            </div>

            <div class="hero-description">
                Discover the joy of homemade Indian food.
                From traditional favourites to everyday meals,
                every dish brings together familiar flavours,
                care and the warmth of a home kitchen.
            </div>

            <div class="hero-note">
                Cooked with experience. Served with love.
            </div>
            """,
            unsafe_allow_html=True
        )

    with hero_right:

        if data["dishes"] and data["dishes"][0].get("photo"):

            st.image(
                photo_url(data["dishes"][0]["photo"]),
                use_container_width=True
            )

        else:

            st.markdown(
                """
                <div style="
                    background:#F7F3ED;
                    border-radius:12px;
                    padding:65px 20px;
                    text-align:center;
                ">
                    <div style="font-size:55px;">🍲</div>
                    <p style="color:#A47745;">
                        A warm welcome from our kitchen
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.write("")
    st.divider()

    # ---------------- DISH COLLECTION ----------------

    st.markdown(
        '<div class="section-label">FROM OUR KITCHEN</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-heading">Our Homemade Dishes</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Explore our food and share your experience with us."
    )

    st.write("")

    if not data["dishes"]:

        st.info(
            "Our dishes will appear here soon. Please visit again!"
        )

    for dish in data["dishes"]:

        dish_comments = dish.get("comments", [])

        # ---------------- DISH PRESENTATION ----------------

        image_col, details_col = st.columns(
            [1, 1.35],
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
                f"### {html.escape(dish.get('name', 'Untitled Dish'))}"
            )

            st.write(
                dish.get("description", "")
            )

            st.caption(
                f"⭐ Customer reviews: {len(dish_comments)}"
            )

        # ---------------- CUSTOMER REVIEWS ----------------

        st.markdown("**Customer Reviews**")

        if dish_comments:

            for comment in dish_comments:

                rating = max(
                    1,
                    min(5, int(comment.get("rating", 5)))
                )

                customer_name = html.escape(
                    str(comment.get("name", "Guest"))
                )

                st.markdown(
                    f"**{customer_name}** "
                    f"· {'⭐' * rating}"
                )

                st.write(comment.get("text", ""))

                st.divider()

        else:

            st.caption(
                "Be the first to share your experience."
            )

        # ---------------- COMMENT FORM ----------------

        if total_comments < MAX_COMMENTS:

            with st.expander("Write a review"):

                with st.form(
                    f"comment_form_{dish['id']}",
                    clear_on_submit=True
                ):

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
                        placeholder="Tell us what you thought...",
                        key=f"text_{dish['id']}"
                    )

                    submitted = st.form_submit_button(
                        "Post Review",
                        use_container_width=True
                    )

                    if submitted:

                        if not comment_text.strip():

                            st.warning("Please write a comment.")

                        else:

                            try:

                                latest_data = load_data()

                                if count_comments(latest_data) >= MAX_COMMENTS:

                                    st.warning(
                                        "The 30-comment limit has been reached."
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

                                        st.error("Dish not found.")

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
                                            "Your review has been published!"
                                        )

                                        st.rerun()

                            except Exception as e:

                                st.error(
                                    f"Unable to publish review: {e}"
                                )

        else:

            st.info("The maximum of 30 comments has been reached.")

        st.divider()

    # =================================================
    # ABOUT ANJALI
    # =================================================

    st.write("")

    st.divider()

    about_left, about_right = st.columns(
        [1, 2],
        gap="large",
        vertical_alignment="center"
    )

    with about_left:

        st.markdown(
            """
            <div style="
                background:#F7F3ED;
                border-radius:12px;
                padding:45px 15px;
                text-align:center;
            ">
                <div style="font-size:65px;">❤️</div>
                <p style="
                    color:#A47745;
                    font-family:Georgia,serif;
                    font-size:20px;
                    font-style:italic;
                ">
                    Made with love
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with about_right:

        st.markdown(
            '<div class="section-label">OUR STORY</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="section-heading">Meet Anjali</div>',
            unsafe_allow_html=True
        )

        st.write(
            """
            Anjali's Kitchen is built around a simple love for
            homemade Indian food.

            With more than 15 years of cooking experience,
            Anjali brings traditional flavours, everyday
            favourites and the warmth of home cooking to
            every dish.

            This kitchen is a place where food is prepared
            with patience, care and a passion for sharing
            good meals with others.
            """
        )

        st.markdown(
            """
            <p style="
                color:#A47745;
                font-family:Georgia,serif;
                font-size:18px;
                font-style:italic;
            ">
                "Good food brings people together."
            </p>
            """,
            unsafe_allow_html=True
        )

        st.write("")

        st.image(
            "https://raw.githubusercontent.com/iamssaroj/my-mothers-kitchen/main/images/anjali-mother.jpeg",
            width=260
            "https://raw.githubusercontent.com/iamssaroj/my-mothers-kitchen/main/images/anjali-mother(1).jpeg",
            width=260
        )


# =====================================================
# 10. ADMIN PAGE
# =====================================================

elif page == "Admin":

    st.markdown("## Admin Panel")

    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    # ---------------- LOGIN ----------------

    if not st.session_state.admin_logged_in:

        st.write("Login to manage your website.")

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

        st.success("Admin logged in.")

        st.divider()

        # ---------------- SUMMARY ----------------

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

        # ---------------- ADD DISH ----------------

        st.markdown("### Add New Dish")

        with st.form("add_dish", clear_on_submit=True):

            dish_name = st.text_input("Dish Name")

            description = st.text_area("Dish Description")

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

                    st.error("Please upload a photograph.")

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

        # ---------------- EDIT / DELETE DISH ----------------

        st.markdown("### Manage Dishes")

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
                    "Description",
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

                        st.error("Dish name cannot be empty.")

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

                            st.success("Dish updated!")
                            st.rerun()

                        except Exception as e:

                            st.error(f"Update failed: {e}")

            if st.button(
                "Delete This Dish",
                type="primary"
            ):

                data["dishes"] = [
                    d for d in data["dishes"]
                    if d["id"] != selected_id
                ]

                try:

                    save_data(data)

                    st.success(
                        "Dish and its comments deleted."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(f"Deletion failed: {e}")

        else:

            st.info("No dishes added yet.")

        st.divider()

        # ---------------- DELETE COMMENTS ----------------

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
                    f"{comment_items[i]['comment_text'][:40]}"
                )
            )

            selected_item = comment_items[selected_comment]

            st.write(selected_item["comment_text"])

            if st.button("Delete Selected Comment"):

                for dish in data["dishes"]:

                    if dish["id"] == selected_item["dish_id"]:

                        dish["comments"] = [
                            c for c in dish.get("comments", [])
                            if c["id"] != selected_item["comment_id"]
                        ]

                try:

                    save_data(data)

                    st.success("Comment deleted.")
                    st.rerun()

                except Exception as e:

                    st.error(f"Deletion failed: {e}")

        else:

            st.caption("No comments available.")


# =====================================================
# 11. FOOTER
# =====================================================

st.divider()

st.markdown(
    """
    <div class="site-footer">
        Anjali's Kitchen · Homemade with love ❤️
    </div>
    """,
    unsafe_allow_html=True
)
