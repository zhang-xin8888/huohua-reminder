"""
抖音火花提醒工具 — Streamlit 网页前端
功能：多人独立面板，管理火花好友、提醒设置、每日续火花标记
"""
import json
import os
from datetime import date

import streamlit as st

# 用户数据目录（与脚本同级的 user_data 文件夹）
USER_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_data")


def sanitize_filename(name: str) -> str:
    """清理 Windows 文件名非法字符"""
    for ch in '\\/:*?"<>|':
        name = name.replace(ch, "_")
    return name.strip() or "user"


def get_user_file(nickname: str) -> str:
    """根据昵称返回用户数据文件路径"""
    return os.path.join(USER_DATA_DIR, f"{sanitize_filename(nickname)}.json")


def load_user(nickname: str) -> dict:
    """加载用户数据，不存在则返回默认结构"""
    path = get_user_file(nickname)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    # 默认用户数据结构
    return {
        "nickname": nickname,
        "reminder_time": "09:00",
        "sc_sendkey": "",
        "pushed_today": False,
        "last_push_date": "",
        "last_reset_date": "",
        "friends": [],
    }


def save_user(data: dict):
    """保存用户数据到独立 JSON 文件"""
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    path = get_user_file(data["nickname"])
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def check_daily_reset(user: dict) -> dict:
    """每日重置：done_today + pushed_today（App 端也检查，防止数据不一致）"""
    today = date.today().isoformat()
    if user.get("last_reset_date") != today:
        for fr in user.get("friends", []):
            fr["done_today"] = False
        user["pushed_today"] = False
        user["last_reset_date"] = today
    return user


def main():
    st.set_page_config(page_title="抖音火花提醒", page_icon="🔥", layout="centered")
    st.title("🔥 抖音火花提醒")

    # --- 昵称入口（无密码） ---
    if "nickname" not in st.session_state:
        st.subheader("输入昵称进入个人面板")
        nick = st.text_input("昵称", placeholder="你的昵称")
        if st.button("进入", type="primary"):
            if nick.strip():
                st.session_state.nickname = nick.strip()
                st.rerun()
            else:
                st.warning("昵称不能为空")
        return

    nickname = st.session_state.nickname
    user = load_user(nickname)
    user = check_daily_reset(user)

    # --- 顶部栏：用户名 + 退出 ---
    col1, col2 = st.columns([5, 1])
    with col1:
        st.write(f"👤 当前用户：**{nickname}**")
    with col2:
        if st.button("退出"):
            del st.session_state.nickname
            st.rerun()

    st.divider()

    # --- 提醒设置 ---
    st.subheader("⚙️ 提醒设置")
    user["reminder_time"] = st.text_input(
        "每日提醒时间 (HH:MM)",
        value=user.get("reminder_time", "09:00"),
        help="24小时制，如 09:00、21:30",
    )
    user["sc_sendkey"] = st.text_input(
        "Server 酱 SendKey",
        value=user.get("sc_sendkey", ""),
        help="在 sct.ftqq.com 登录后获取 SendKey，填入即可通过微信接收推送",
    ).strip()

    if not user["sc_sendkey"]:
        st.warning("⚠️ 请设置 Server 酱 SendKey，否则无法接收微信推送提醒")

    st.divider()

    # --- 火花好友管理 ---
    st.subheader("👥 火花好友")

    # 新增好友表单
    with st.expander("➕ 新增好友"):
        with st.form("add_friend_form"):
            new_name = st.text_input("好友名称 *")
            new_days = st.number_input("火花天数", min_value=0, value=0, step=1)
            new_note = st.text_input("备注（可选）")
            if st.form_submit_button("添加"):
                if not new_name.strip():
                    st.warning("好友名称不能为空")
                else:
                    user["friends"].append({
                        "name": new_name.strip(),
                        "days": int(new_days),
                        "note": new_note.strip(),
                        "remind_enabled": True,
                        "done_today": False,
                    })
                    save_user(user)
                    st.success(f"已添加好友：{new_name.strip()}")
                    st.rerun()

    # 好友列表
    if not user["friends"]:
        st.info("还没有火花好友，点击「➕ 新增好友」添加。")
    else:
        for i, fr in enumerate(user["friends"]):
            with st.container():
                cols = st.columns([1.2, 1.8, 1, 2, 1, 0.4])
                with cols[0]:
                    fr["done_today"] = st.checkbox(
                        "今日已续", value=fr["done_today"], key=f"done_{i}"
                    )
                with cols[1]:
                    st.write(f"**{fr['name']}**")
                with cols[2]:
                    st.write(f"🔥{fr['days']}天")
                with cols[3]:
                    st.write(fr["note"] if fr["note"] else "—")
                with cols[4]:
                    fr["remind_enabled"] = st.checkbox(
                        "提醒", value=fr["remind_enabled"], key=f"remind_{i}"
                    )
                with cols[5]:
                    if st.button("✕", key=f"del_{i}"):
                        user["friends"].pop(i)
                        save_user(user)
                        st.rerun()
                st.divider()

    # 自动保存（捕获所有 widget 变更）
    save_user(user)


if __name__ == "__main__":
    main()
