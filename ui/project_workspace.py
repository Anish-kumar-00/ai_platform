import streamlit as st
from tools import project_manager
from tools.file_manager import FileManager, FileError


def _bump():
    st.session_state.ver = st.session_state.get("ver", 0) + 1


def _flash(msg):
    st.session_state.flash = msg
    _bump()
    st.rerun()


def render_workspace(project):
    pid = project["id"]
    fm = FileManager(project_manager.project_dir(project))
    files = fm.list_files()
    ver = st.session_state.get("ver", 0)

    if st.session_state.get("flash"):
        st.success(st.session_state.pop("flash"))

    st.subheader(f"📁 {project['name']}")
    st.caption("Files are temporary on Streamlit Cloud. Download the ZIP to keep them.")
    c1, c2 = st.columns(2)
    c1.metric("Files", len(files))
    c2.download_button("⬇ Download ZIP", project_manager.zip_bytes(project),
                       file_name=f"{project['slug']}.zip", mime="application/zip",
                       use_container_width=True)

    with st.expander("Folder structure"):
        st.code(fm.tree() or "(empty project)", language=None)

    mode = st.radio("Action", ["Edit", "New", "Upload"], horizontal=True,
                    label_visibility="collapsed", key=f"mode_{pid}")

    if mode == "Edit":
        if not files:
            st.info("No files yet. Use New or Upload.")
            return
        sel = st.selectbox("File", files, key=f"sel_{pid}")
        try:
            content = fm.read(sel)
        except FileError as e:
            st.warning(str(e))
            return
        new = st.text_area("Content", content, height=400, key=f"ta_{pid}_{ver}_{sel}")
        if st.button("💾 Save", use_container_width=True):
            try:
                fm.write(sel, new)
                st.success("Saved.")
            except FileError as e:
                st.error(str(e))
        st.divider()
        confirm = st.checkbox(f"Confirm: delete {sel}", key=f"cf_{pid}_{ver}_{sel}")
        if st.button("🗑 Delete file", disabled=not confirm):
            try:
                fm.delete(sel)
                _flash(f"Deleted {sel}")
            except FileError as e:
                st.error(str(e))

    elif mode == "New":
        path = st.text_input("File path", placeholder="src/main.py", key=f"np_{pid}_{ver}")
        body = st.text_area("Content (optional)", height=200, key=f"nc_{pid}_{ver}")
        if st.button("Create file", use_container_width=True):
            try:
                if fm.exists(path):
                    st.error("File already exists. Use Edit.")
                else:
                    fm.write(path, body)
                    _flash(f"Created {path}")
            except FileError as e:
                st.error(str(e))
        st.divider()
        folder = st.text_input("Folder path", placeholder="src/utils", key=f"nf_{pid}_{ver}")
        if st.button("Create folder", use_container_width=True):
            try:
                fm.make_dir(folder)
                _flash(f"Created folder {folder}")
            except FileError as e:
                st.error(str(e))

    else:
        st.caption("A .zip upload is extracted into the project automatically.")
        ups = st.file_uploader("Upload files", accept_multiple_files=True,
                               key=f"up_{pid}_{ver}")
        if ups and st.button("Add to project", use_container_width=True):
            added, errors = 0, []
            for f in ups:
                try:
                    data = f.getvalue()
                    if f.name.lower().endswith(".zip"):
                        added += fm.extract_zip(data)
                    else:
                        fm.write_bytes(f.name, data)
                        added += 1
                except FileError as e:
                    errors.append(f"{f.name}: {e}")
            if errors:
                st.error("\n".join(errors))
            if added:
                _flash(f"Added {added} file(s)")
