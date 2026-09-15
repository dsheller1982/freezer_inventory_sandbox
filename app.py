import streamlit as st

from database import (
    DatabaseError,
    add_new_item,
    fetch_inventory,
    fetch_transactions,
    remove_item,
    reset_demo,
    restock_item,
)


st.set_page_config(page_title="Freezer Inventory Sandbox", page_icon="❄️", layout="wide")


def flash(message: str) -> None:
    st.session_state["flash_message"] = message


def show_flash() -> None:
    message = st.session_state.pop("flash_message", None)
    if message:
        st.success(message, icon="✅")


def moneyless_quantity(value) -> str:
    number = float(value)
    return str(int(number)) if number.is_integer() else f"{number:g}"


st.title("❄️ Freezer Inventory Sandbox")
st.caption("A disposable portfolio demo. Feel free to add, restock, remove, or reset items—no real household data is used.")
show_flash()

try:
    inventory = fetch_inventory()
except DatabaseError as exc:
    st.error(f"The demo database is unavailable: {exc}")
    st.stop()

total_units = sum(float(item["quantity"]) for item in inventory)
locations = len({item["location"] for item in inventory})
categories = len({item["category"] for item in inventory})
metric1, metric2, metric3, metric4 = st.columns(4)
metric1.metric("Distinct items", len(inventory))
metric2.metric("Total quantity", moneyless_quantity(total_units))
metric3.metric("Locations", locations)
metric4.metric("Categories", categories)

inventory_tab, remove_tab, add_tab, history_tab, about_tab = st.tabs(
    ["📦 Inventory", "➖ Remove", "➕ Add / Restock", "🧾 Transactions", "ℹ️ About"]
)

with inventory_tab:
    st.subheader("Current inventory")
    search = st.text_input("Search inventory", placeholder="Item, category, or location")
    filtered = inventory
    if search:
        needle = search.casefold()
        filtered = [
            item
            for item in inventory
            if needle in item["item_name"].casefold()
            or needle in item["category"].casefold()
            or needle in item["location"].casefold()
        ]
    display_rows = [
        {
            "Item": item["item_name"],
            "Quantity": float(item["quantity"]),
            "Location": item["location"],
            "Category": item["category"],
            "Expiration": item["exp_date"],
        }
        for item in filtered
    ]
    st.dataframe(display_rows, use_container_width=True, hide_index=True)

with remove_tab:
    st.subheader("Use or remove an item")
    if not inventory:
        st.info("There is nothing to remove. Add an item or reset the demo data.")
    else:
        options = {
            f"{item['item_name']} · {item['location']} · Qty {moneyless_quantity(item['quantity'])}": item
            for item in inventory
        }
        selected_label = st.selectbox("Item", options, key="remove_item")
        selected = options[selected_label]
        available = max(1, int(float(selected["quantity"])))
        amount = st.number_input("Quantity to remove", min_value=1, max_value=available, value=1, step=1)
        if st.button("Confirm removal", type="primary", use_container_width=True):
            try:
                result = remove_item(selected["id"], amount)
                suffix = " The item reached zero and was removed from inventory." if result["deleted"] else ""
                flash(
                    f"Removed {moneyless_quantity(result['change'])} × {result['item_name']}. "
                    f"Quantity: {moneyless_quantity(result['before'])} → {moneyless_quantity(result['after'])}.{suffix}"
                )
                st.rerun()
            except DatabaseError as exc:
                st.error(str(exc))

with add_tab:
    st.subheader("Add or restock inventory")
    mode = st.radio("Action", ["Restock an existing item", "Add a new item"], horizontal=True)
    if mode == "Restock an existing item" and inventory:
        options = {
            f"{item['item_name']} · {item['location']} · Qty {moneyless_quantity(item['quantity'])}": item
            for item in inventory
        }
        selected_label = st.selectbox("Item", options, key="restock_item")
        selected = options[selected_label]
        amount = st.number_input("Quantity to add", min_value=1, max_value=999, value=1, step=1)
        if st.button("Update stock", type="primary", use_container_width=True):
            try:
                result = restock_item(selected["id"], amount)
                flash(
                    f"Added {moneyless_quantity(result['change'])} × {result['item_name']}. "
                    f"Quantity: {moneyless_quantity(result['before'])} → {moneyless_quantity(result['after'])}."
                )
                st.rerun()
            except DatabaseError as exc:
                st.error(str(exc))
    elif mode == "Restock an existing item":
        st.info("No existing items are available. Add a new item instead.")
    else:
        known_locations = sorted({item["location"] for item in inventory})
        known_categories = sorted({item["category"] for item in inventory})
        with st.form("new_item_form", clear_on_submit=False):
            name = st.text_input("Item name", max_chars=100, placeholder="Pork shoulder")
            quantity = st.number_input("Initial quantity", min_value=1, max_value=999, value=1, step=1)
            location_options = known_locations + ["Add a new location"]
            location_choice = st.selectbox("Location", location_options)
            location = (
                st.text_input("New location", max_chars=50)
                if location_choice == "Add a new location"
                else location_choice
            )
            category_options = known_categories + ["Add a new category"]
            category_choice = st.selectbox("Category", category_options)
            category = (
                st.text_input("New category", max_chars=50)
                if category_choice == "Add a new category"
                else category_choice
            )
            expiration = st.date_input("Expiration date (optional)", value=None)
            submitted = st.form_submit_button("Insert new item", type="primary", use_container_width=True)
        if submitted:
            try:
                result = add_new_item(name, quantity, location, category, expiration)
                flash(
                    f"Added {moneyless_quantity(result['after'])} × {result['item_name']} "
                    f"to {result['location']}."
                )
                st.rerun()
            except DatabaseError as exc:
                st.error(str(exc))

with history_tab:
    st.subheader("Recent transaction history")
    st.caption("Every add, restock, removal, zero-quantity deletion, and reset is recorded here.")
    try:
        history = fetch_transactions(limit=200)
        rows = [
            {
                "Time (UTC)": row["created_at"],
                "Action": row["action"].replace("_", " ").title(),
                "Item": row["item_name"],
                "Change": float(row["quantity_change"]),
                "Before": None if row["quantity_before"] is None else float(row["quantity_before"]),
                "After": None if row["quantity_after"] is None else float(row["quantity_after"]),
                "Location": row["location"],
            }
            for row in history
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)
    except DatabaseError as exc:
        st.error(str(exc))

with about_tab:
    st.subheader("About this demo")
    st.markdown(
        """
        This is an isolated demonstration copy of a household freezer inventory application.
        It uses synthetic data and demo-only database credentials. Visitors can exercise full
        create, read, update, and delete behavior without any connection to the private system.

        The database automatically returns to a known seed state on a schedule. You can also
        reset it immediately below.
        """
    )
    confirm_reset = st.checkbox("I understand this replaces all current demo changes.")
    if st.button("Reset demo data now", disabled=not confirm_reset):
        try:
            reset_demo()
            flash("The sandbox was reset to its original demonstration data.")
            st.rerun()
        except DatabaseError as exc:
            st.error(str(exc))

