document.addEventListener('DOMContentLoaded', function() {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ 
            video: { 
                facingMode: 'user',
                width: { ideal: 1280 },
                height: { ideal: 720 }
            } 
        })
        .then(stream => {
            const video = document.getElementById('mobile-video');
            video.srcObject = stream;
            
            document.getElementById('capture-mobile').onclick = () => {
                const canvas = document.createElement('canvas');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                canvas.getContext('2d').drawImage(video, 0, 0);
                
                canvas.toBlob(blob => {
                    const formData = new FormData();
                    formData.append('image', blob);
                    
                    fetch('/auth/mobile-verification/', {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => response.json())
                    .then(data => {
                        if(data.status === 'success') {
                            window.location.href = data.redirect_url;
                        } else {
                            alert(data.message);
                        }
                    });
                }, 'image/jpeg');
            };
        })
        .catch(error => {
            console.error('Camera access error:', error);
            alert('Unable to access camera');
        });
    }
});
