const tree_photo = document.getElementsByClassName("tree-photo");
console.log(tree_photo)

// HTMLから要素を取得
const container = document.getElementById('imgset'); // #imgsetコンテナを取得
const ballElements = document.querySelectorAll('.ball');

// コンテナのサイズを取得
let containerWidth = container.clientWidth;
let containerHeight = container.clientHeight;

// ボールの半径と直径を定義
const radius = 32;
const diameter = radius * 2;

// 各ボールの状態を格納する配列
const balls = [];

// 各ボール要素に対して初期設定を行う
ballElements.forEach(element => {
    // コンテナ内にランダムな初期位置を生成
    const initialX = Math.random() * (containerWidth - diameter);
    const initialY = Math.random() * (containerHeight - diameter);

    // -4から4の間でランダムな速度を生成（少し遅めに調整）
    const initialDx = (Math.random() - 0.5) * 2 || 1;
    const initialDy = (Math.random() - 0.5) * 2 || 1;

    balls.push({
        element: element,
        diameter: diameter,
        x: initialX,
        y: initialY,
        dx: initialDx, // 水平方向の速度
        dy: initialDy  // 垂直方向の速度
    });
});

/**
 * アニメーションを更新する関数
 */
function animate() {
    balls.forEach(ball => {
        containerWidth = container.clientWidth;
        containerHeight = container.clientHeight;
        // 1. 位置を更新
        ball.x += ball.dx;
        ball.y += ball.dy;

        // 2. 壁との衝突判定（基準をコンテナの幅と高さに変更）
        if (ball.x <= 0 || ball.x >= containerWidth - ball.diameter) {
            ball.dx *= -1;
        }
        if (ball.y <= 0 || ball.y >= containerHeight - ball.diameter) {
            ball.dy *= -1;
        }

        // 念のため、はみ出さないように位置を微調整
        ball.x = Math.max(0, Math.min(ball.x, containerWidth - ball.diameter));
        ball.y = Math.max(0, Math.min(ball.y, containerHeight - ball.diameter));

        // 3. 実際の要素のスタイルに反映
        ball.element.style.left = `${ball.x}px`;
        ball.element.style.top = `${ball.y}px`;
    });

    // 次の描画タイミングで再度animate関数を呼び出す
    requestAnimationFrame(animate);
}

// アニメーションを開始
animate();