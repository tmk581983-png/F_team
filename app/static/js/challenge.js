// タイマーと開始ボタンに使う要素を指定
const setTime = document.getElementById('setTime');
const start = document.getElementById("start");
const backbutton = document.getElementById("back-button");

let startTime;
// クリックした時の動作の設定
start.addEventListener('click',() => {
  startTime = Date.now();
  console.log(startTime);
  console.log(new Date(startTime))
  countUp();
  backbutton.style.pointerEvents = "none";
  start.style.pointerEvents = "none";
})

// カウントアップタイマーの設定
function countUp() {
  const studytime = Date.now() - startTime;　

  const d=new Date(studytime);
  // もし経過時間を追加するならば、下を使う
  // const hours = Math.floor(studytime /1000 / 60 /60)
  const m=String(d.getMinutes()).padStart(2,"0");
  const s=String(d.getSeconds()).padStart(2,"0");
  // const ms=String(d.getMilliseconds()).padStart(3,"0");
  setTime.textContent = `${m}:${s}/10:00`;

  // タイマー設定：10分は600000、テストは5000　単位はミリ秒
  const resultReport = document.getElementById("resultReport");

  if (studytime >= 5000) {
      resultReport.classList.remove("disabled");
      resultReport.textContent="チャレンジ達成!!"
  }
// 画面更新のたびにcountUpを実行してという指示
  requestAnimationFrame(countUp);

}




