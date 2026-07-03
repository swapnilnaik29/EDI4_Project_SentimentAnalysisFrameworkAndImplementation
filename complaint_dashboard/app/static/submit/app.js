document.addEventListener("DOMContentLoaded", () => {
    // Initialize Lucide Icons
    lucide.createIcons();

    // Elements
    const form = document.getElementById("complaintForm");
    const complaintText = document.getElementById("complaintText");
    const userType = document.getElementById("userType");
    const complaintSource = document.getElementById("complaintSource");
    const locationInput = document.getElementById("location");
    const dateInput = document.getElementById("complaintDate");
    const timeInput = document.getElementById("complaintTime");
    const submitBtn = document.getElementById("submitBtn");
    const btnText = submitBtn.querySelector(".btn-text");
    const btnLoader = submitBtn.querySelector(".btn-loader");
    const toastContainer = document.getElementById("toastContainer");

    // Pre-populate date and time with local values
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, "0");
    const day = String(now.getDate()).padStart(2, "0");
    const hours = String(now.getHours()).padStart(2, "0");
    const minutes = String(now.getMinutes()).padStart(2, "0");

    dateInput.value = `${year}-${month}-${day}`;
    timeInput.value = `${hours}:${minutes}`;

    // Text counter dynamic updating
    complaintText.addEventListener("input", () => {
        const textLength = complaintText.value.length;
        const counter = document.querySelector(".character-counter");
        if (textLength < 10) {
            counter.textContent = `Min 10 characters required (${textLength}/10)`;
            counter.style.color = "var(--color-danger)";
        } else {
            counter.textContent = `${textLength} characters`;
            counter.style.color = "var(--color-success)";
        }
    });

    // Form submission
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const text = complaintText.value.trim();
        if (text.length < 10) {
            showToast("Complaint description is too short. Please provide more details.", "error");
            return;
        }

        // Gather data
        const payload = {
            complaint_text: text,
            complaint_date: dateInput.value,
            complaint_time: timeInput.value ? `${timeInput.value}:00` : null, // format as HH:MM:SS
            location: locationInput.value.trim() || "Online",
            user_type: userType.value,
            complaint_source: complaintSource.value
        };

        // Loading state
        submitBtn.disabled = true;
        btnText.textContent = "Processing Complaint...";
        btnLoader.style.display = "block";

        try {
            const response = await fetch("/api/complaints", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                const data = await response.json();
                showToast("Ticket submitted and routed successfully!", "success");
                form.reset();
                // Reset date/time defaults
                dateInput.value = `${year}-${month}-${day}`;
                timeInput.value = `${hours}:${minutes}`;
                document.querySelector(".character-counter").textContent = "Min 10 characters required";
                document.querySelector(".character-counter").style.color = "var(--color-text-muted)";
            } else {
                const err = await response.json();
                showToast(`Submission failed: ${err.detail || "Server error"}`, "error");
            }
        } catch (error) {
            console.error(error);
            showToast("Connection to backend lost. Make sure FastAPI server is running.", "error");
        } finally {
            // Restore button state
            submitBtn.disabled = false;
            btnText.textContent = "Submit Support Ticket";
            btnLoader.style.display = "none";
        }
    });

    // Toast manager
    function showToast(message, type = "success") {
        const toast = document.createElement("div");
        toast.className = `toast ${type}`;
        
        const iconName = type === "success" ? "check-circle" : "alert-circle";
        toast.innerHTML = `
            <i data-lucide="${iconName}"></i>
            <span class="toast-message">${message}</span>
        `;
        
        toastContainer.appendChild(toast);
        lucide.createIcons(); // Instantiates lucide within newly added toast HTML

        // Slide away and delete
        setTimeout(() => {
            toast.style.animation = "slideIn 0.4s reverse forwards";
            setTimeout(() => {
                toast.remove();
            }, 400);
        }, 4000);
    }
});
