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
  start.classList.add("time-btn-2","blink")
  start.textContent="学習中・・・"
  
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
  const memo = document.getElementsByClassName("memo")

  if (studytime >= 10000) {
      // テスト用 強制的に10分表示
      setTime.textContent = `10:00/10:00`;
      resultReport.classList.remove("disabled","hidden" );
      resultReport.textContent="✔︎ 達成！結果を投稿する";
      start.classList.add("hidden");
      setTime.classList.add("set-time-complete");
      memo[0].textContent="10分間お疲れさまでした!"
      return;
  }
// 画面更新のたびにcountUpを実行してという指示
  requestAnimationFrame(countUp);

  

}




