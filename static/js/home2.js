const tree_photo = document.getElementsByClassName("tree-photo");
console.log(tree_photo)

const container = document.getElementById('imgset');
const ballElements = document.querySelectorAll('.ball');

let containerWidth = container.clientWidth;
let containerHeight = container.clientHeight;

const radius = 32;
const diameter = radius * 2;

const balls = [];

ballElements.forEach(element => {
    const initialX = Math.random() * (containerWidth - diameter);
    const initialY = Math.random() * (containerHeight - diameter);

    const initialDx = (Math.random() - 0.5) * 2 || 1;
    const initialDy = (Math.random() - 0.5) * 2 || 1;

    balls.push({
        element: element,
        diameter: diameter,
        x: initialX,
        y: initialY,
        dx: initialDx,
        dy: initialDy
    });
});


function animate() {
    balls.forEach(ball => {
        containerWidth = container.clientWidth;
        containerHeight = container.clientHeight;
        ball.x += ball.dx;
        ball.y += ball.dy;

        if (ball.x <= 0 || ball.x >= containerWidth - ball.diameter) {
            ball.dx *= -1;
        }
        if (ball.y <= 0 || ball.y >= containerHeight - ball.diameter) {
            ball.dy *= -1;
        }
        ball.x = Math.max(0, Math.min(ball.x, containerWidth - ball.diameter));
        ball.y = Math.max(0, Math.min(ball.y, containerHeight - ball.diameter));

        ball.element.style.left = `${ball.x}px`;
        ball.element.style.top = `${ball.y}px`;
    });

    requestAnimationFrame(animate);
}

// アニメーションを開始
animate();