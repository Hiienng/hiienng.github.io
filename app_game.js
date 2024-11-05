let questionsData = [];
let currentQuestionIndex = 0;
let score = 0;

// Tải dữ liệu từ tệp JSON
function loadQuestions() {
    fetch("questions_game.json")
        .then(response => {
            if (!response.ok) throw new Error("Không thể tải file JSON.");
            return response.json();
        })
        .then(data => {
            questionsData = data;
            displayQuestion(currentQuestionIndex);
        })
        .catch(error => {
            console.error("Lỗi khi tải file JSON:", error);
            alert("Đã xảy ra lỗi khi tải file JSON: " + error.message);
        });
}

// Hiển thị câu hỏi hiện tại
function displayQuestion(index) {
    const questionData = questionsData[index];
    document.getElementById("questionText").textContent = questionData.question;
    document.getElementById("feedbackText").textContent = "";
    const answerOptions = document.getElementById("answerOptions");
    answerOptions.innerHTML = ""; // Xóa lựa chọn cũ

    // Hiển thị các lựa chọn câu trả lời
    questionData.options.forEach((option, i) => {
        const button = document.createElement("button");
        button.classList.add("option-btn");
        button.textContent = `${i + 1}. ${option}`;
        button.onclick = () => checkAnswer(button, option, questionData.correctAnswer);
        answerOptions.appendChild(button);
    });

    // Cập nhật tiến trình
    document.getElementById("progress").style.width = ((index + 1) / questionsData.length) * 100 + "%";
}

// Kiểm tra câu trả lời
function checkAnswer(selectedButton, userAnswer, correctAnswer) {
    const feedbackText = document.getElementById("feedbackText");

    // Xóa trạng thái đúng/sai của các nút trước đó
    document.querySelectorAll('.option-btn').forEach(btn => {
        btn.classList.remove('correct', 'incorrect');
    });

    // Kiểm tra và cập nhật trạng thái
    if (userAnswer === correctAnswer) {
        selectedButton.classList.add("correct");
        feedbackText.textContent = "Great job!";
        feedbackText.style.color = "#4caf50";
        score++;
    } else {
        selectedButton.classList.add("incorrect");
        feedbackText.textContent = "No sweat, you're still learning!";
        feedbackText.style.color = "#ff5722";

        // Đánh dấu nút đúng
        document.querySelectorAll('.option-btn').forEach(btn => {
            if (btn.textContent.includes(correctAnswer)) {
                btn.classList.add("correct");
            }
        });
    }

    // Chuyển sang câu hỏi tiếp theo sau một khoảng thời gian
    setTimeout(() => {
        currentQuestionIndex++;
        if (currentQuestionIndex < questionsData.length) {
            displayQuestion(currentQuestionIndex);
        } else {
            displayResults();
        }
    }, 2000);
}

// Hiển thị kết quả khi hoàn thành quiz
function displayResults() {
    document.querySelector('.question-section').innerHTML = `<h2>Quiz Completed!</h2>`;
    document.getElementById("answerOptions").innerHTML = `<p>You scored ${score} out of ${questionsData.length}</p>`;
}

document.addEventListener("DOMContentLoaded", loadQuestions);
