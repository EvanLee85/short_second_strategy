import { Card } from "../components/Card.js";
export default { route: "/macro", title: "宏观状态", render() {
  const box=document.createElement("div");
  box.appendChild(Card({ title:"宏观状态", content:"这里展示 /macro/status（后续实现）" }));
  return box;
}};
