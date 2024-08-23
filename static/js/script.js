document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('file-input');
    const uploadButton = document.getElementById('upload-button');
    const loadingMessage = document.getElementById('loading-message');
    const mfccImage = document.getElementById('mfcc-image');
    const resultText = document.getElementById('result-text');
    const imageContainer = document.getElementById('image-container');
    const sendButton = document.getElementById('send-button');
    const uploadButton2 = document.getElementById('upload-button2');
    const fileInput2 = document.getElementById('file-input2');
    const chatInput = document.getElementById('chat-input');
    const chatLog = document.getElementById('chat-log');

    let selectedImages = [];

    // 파일 업로드 버튼 클릭 시 파일 선택 창 열기
    uploadButton.addEventListener('click', function() {
        fileInput.click();
    });

    // 파일 선택 후 업로드 처리
    fileInput.addEventListener('change', function() {
        const file = fileInput.files[0];
        if (file) {
            const formData = new FormData();
            const button1 = document.getElementById('button1');
            const button2 = document.getElementById('button2');
            const button3 = document.getElementById('button3');
            formData.append('file', file);

            loadingMessage.style.display = 'block';
            resultText.textContent = '';

            fetch('/upload', {
                method: 'POST',
                body: formData
            }).then(response => response.json())
              .then(data => {
                  alert(data.message);
                  loadingMessage.style.display = 'none';
                  mfccImage.src = '/uploads/tmp.png';  // MFCC 이미지 표시
                  mfccImage.style.display = 'block';   // MFCC 이미지를 화면에 표시
                  resultText.textContent = data.response_text;
                  button1.textContent = data.aes1;
                  button2.textContent = data.aes2;
                  button3.textContent = data.aes3;
              })
              .catch(error => {
                  console.error('Error:', error);
                  loadingMessage.style.display = 'none';
                  resultText.textContent = 'An error occurred while uploading the file.';
              });
        } else {
            alert('No file selected');
        }
    });

    // 새로운 이미지를 화면에 표시하는 함수
    function displayImages(images) {
        imageContainer.innerHTML = ''; // 기존 이미지 삭제
        images.forEach(imageSrc => {
            const img = document.createElement('img');
            img.src = imageSrc;
            img.addEventListener('click', function() {
                img.classList.toggle('selected');
                if (selectedImages.includes(imageSrc)) {
                    selectedImages = selectedImages.filter(item => item !== imageSrc);
                } else {
                    selectedImages.push(imageSrc);
                }
                sendSelectedImages();
                
            });
            imageContainer.appendChild(img);
        });
    }

    // 선택된 이미지를 서버로 전송하는 함수
    function sendSelectedImages() {        
        fetch('/set_selected_images', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ selected_images: selectedImages })
        }).then(response => response.json())
          .then(data => {              
              console.log('Selected images saved:', data);
          })
          .catch(error => console.error('Error saving selected images:', error));
    }

    // action1, action2, action3 버튼 클릭 시 이미지 로드
    document.getElementById('button1').addEventListener('click', function() {
        loadingMessage.style.display = 'block';
        fetch('/action1', {
            method: 'POST',
        }).then(response => response.json())
          .then(data => {
            
              loadingMessage.style.display = 'none';
              resultText.textContent = data.response_text;
              displayImages(data.images);  // 받은 이미지를 화면에 표시
          })
          .catch(error => console.error('Error fetching action1 data:', error));
    });

    document.getElementById('button2').addEventListener('click', function() {
        loadingMessage.style.display = 'block';
        fetch('/action2', {
            method: 'POST',
        }).then(response => response.json())
          .then(data => {
            loadingMessage.style.display = 'none';
              resultText.textContent = data.response_text;
              displayImages(data.images);  // 받은 이미지를 화면에 표시
          })
          .catch(error => console.error('Error fetching action2 data:', error));
    });

    document.getElementById('button3').addEventListener('click', function() {
        loadingMessage.style.display = 'block';
        fetch('/action3', {
            method: 'POST',
        }).then(response => response.json())
          .then(data => {
            loadingMessage.style.display = 'none';
              resultText.textContent = data.response_text;
              displayImages(data.images);  // 받은 이미지를 화면에 표시
          })
          .catch(error => console.error('Error fetching action3 data:', error));
    });

    document.getElementById('select-button').addEventListener('click', function() { //여기예요여기ㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣㅣ
        loadingMessage.style.display = 'block';
        fetch('/select_img_togpt', {
            method: 'POST',
        }).then(response => response.json())
          .then(data => {
            loadingMessage.style.display = 'none';
            alert(data.response);
            if(data.image == "None")
            {
                selectedImages = [];
            }
            else
            {
                displayImages(data.image);
                addMessageToLog('Assistant', "해당 사진/그림의 어떤 점이 음악과 잘 어울린다고 생각하시나요?");
            }
          })
          .catch(error => console.error('Error fetching action3 data:', error));
    });

    // 메시지 전송 처리
    sendButton.addEventListener('click', function() {
        const userMessage = chatInput.value.trim();

        if (userMessage !== "") {
            addMessageToLog('User', userMessage);

            // 텍스트 메시지를 서버로 전송
            fetch('/process_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: userMessage }),
            })
            .then(response => response.json())
            .then(data => {
                addMessageToLog('Assistant', data.response);
                chatLog.scrollTop = chatLog.scrollHeight; // 스크롤을 맨 아래로 이동
            })
            .catch(error => console.error('Error:', error));

            chatInput.value = ""; // 입력 필드 초기화
        }
    });

    function addMessageToLog(sender, message) {
        const messageElement = document.createElement('div');
        messageElement.classList.add(sender.toLowerCase() + '-message');
        messageElement.textContent = sender + ": " + message;
        chatLog.appendChild(messageElement);
    }

    // 파일 업로드 버튼 클릭 시 파일 선택 창 열기
    uploadButton2.addEventListener('click', function() {
        fileInput2.click();
    });

    // 파일 선택 후 업로드 처리
    fileInput2.addEventListener('change', function() {
        const file = fileInput2.files[0];
        if (file) {
            const formData = new FormData();
            formData.append('file', file);

            loadingMessage.style.display = 'block';
            resultText.textContent = '';

            fetch('/upload_file', {
                method: 'POST',
                body: formData
            }).then(response => response.json())
                .then(data => {
                    alert(data.message);
                    loadingMessage.style.display = 'none';
                    resultText.textContent = data.response_text;
                })
                .catch(error => {
                    console.error('Error:', error);
                    loadingMessage.style.display = 'none';
                    resultText.textContent = 'An error occurred while uploading the file.';
                });
        } else {
            alert('No file selected');
        }
    });
});
