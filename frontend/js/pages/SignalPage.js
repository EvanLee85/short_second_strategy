import { Card } from "../components/Card.js";
export default { route: "/signal", title: "入场信号", render() {
  const box=document.createElement("div");
  box.appendChild(Card({ title:"入场信号", content:"这里发起 /trades/signal（后续实现）" }));
  return box;
}};
