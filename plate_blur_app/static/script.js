const form = document.getElementById('uploadForm');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
let image = new Image();
let startX, startY, isDrawing = false;

form.onsubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData(form);
    const method = formData.get('method');

    const res = await fetch('/upload', {
        method: 'POST',
        body: formData
    });

    const data = await res.json();
    const filename = data.filename;

    if (method === 'ai') {
        document.getElementById('processedImage').src = `/processed/${filename}`;
        document.getElementById('processedImage').style.display = 'block';
    } else {
        image.src = `/uploads/${filename}`;
    }
};

image.onload = () => {
    canvas.width = image.width;
    canvas.height = image.height;
    ctx.drawImage(image, 0, 0);
};

canvas.addEventListener('mousedown', (e) => {
    startX = e.offsetX;
    startY = e.offsetY;
    isDrawing = true;
});

canvas.addEventListener('mouseup', (e) => {
    if (isDrawing) {
        const endX = e.offsetX;
        const endY = e.offsetY;
        const w = endX - startX;
        const h = endY - startY;

        const imgData = ctx.getImageData(startX, startY, w, h);
        let data = imgData.data;
        for (let y = 0; y < h; y += 10) {
            for (let x = 0; x < w; x += 10) {
                const i = (y * w + x) * 4;
                const r = data[i], g = data[i+1], b = data[i+2];
                for (let dy = 0; dy < 10; dy++) {
                    for (let dx = 0; dx < 10; dx++) {
                        const j = ((y+dy) * w + (x+dx)) * 4;
                        data[j] = r;
                        data[j+1] = g;
                        data[j+2] = b;
                    }
                }
            }
        }
        ctx.putImageData(imgData, startX, startY);
    }
    isDrawing = false;
});