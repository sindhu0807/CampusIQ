document.addEventListener("DOMContentLoaded", function () {
    // Student directory: search by name or student ID.
    const studentSearch = document.getElementById("studentSearch");
    const departmentFilter = document.getElementById("departmentFilter");
    const studentsTable = document.getElementById("studentsTable");
    const noStudentsFound = document.getElementById("noStudentsFound");

    function filterStudents() {
        if (!studentsTable) return;

        const searchText = studentSearch
            ? studentSearch.value.trim().toLowerCase()
            : "";

        const department = departmentFilter
            ? departmentFilter.value.toLowerCase()
            : "";

        const rows = studentsTable.querySelectorAll("tbody tr");
        let visibleCount = 0;

        rows.forEach(function (row) {
            const rowText = row.textContent.toLowerCase();
            const rowDepartment = (
                row.dataset.department || ""
            ).toLowerCase();

            const matchesSearch = rowText.includes(searchText);
            const matchesDepartment =
                !department || rowDepartment === department;

            const visible = matchesSearch && matchesDepartment;
            row.hidden = !visible;

            if (visible) visibleCount++;
        });

        if (noStudentsFound) {
            noStudentsFound.hidden = visibleCount !== 0;
        }
    }

    if (studentSearch) {
        studentSearch.addEventListener("input", filterStudents);
    }

    if (departmentFilter) {
        departmentFilter.addEventListener("change", filterStudents);
    }

    // Risk monitoring: search the displayed risk records.
    const riskSearch = document.getElementById("riskSearch");
    const riskTable = document.getElementById("riskTable");
    const noRiskFound = document.getElementById("noRiskFound");

    if (riskSearch && riskTable) {
        riskSearch.addEventListener("input", function () {
            const query = riskSearch.value.trim().toLowerCase();
            const rows = riskTable.querySelectorAll("tbody tr");
            let visibleCount = 0;

            rows.forEach(function (row) {
                const visible = row.textContent.toLowerCase().includes(query);
                row.hidden = !visible;

                if (visible) visibleCount++;
            });

            if (noRiskFound) {
                noRiskFound.hidden = visibleCount !== 0;
            }
        });
    }

    // Student segments: search by name, ID, department, or segment.
    const segmentSearch = document.getElementById("segmentSearch");
    const segmentTable = document.getElementById("segmentTable");

    if (segmentSearch && segmentTable) {
        segmentSearch.addEventListener("input", function () {
            const query = segmentSearch.value.trim().toLowerCase();
            const rows = segmentTable.querySelectorAll("tbody tr");

            rows.forEach(function (row) {
                row.hidden = !row.textContent.toLowerCase().includes(query);
            });
        });
    }
});
document.addEventListener("click", function (event) {
    const button = event.target.closest("[data-toggle-password]");

    if (!button) return;

    const inputId = button.getAttribute("data-toggle-password");
    const passwordInput = document.getElementById(inputId);

    if (!passwordInput) return;

    const showingPassword = passwordInput.type === "password";

    passwordInput.type = showingPassword ? "text" : "password";
    button.textContent = showingPassword ? "Hide" : "Show";
    button.setAttribute("aria-pressed", String(showingPassword));
    button.setAttribute(
        "aria-label",
        showingPassword ? "Hide password" : "Show password"
    );
});
