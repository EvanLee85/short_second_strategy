import { Card } from "../components/Card.js";
export default { route: "/paper", title: "纸上交易", render() {
  const box=document.createElement("div");
  box.appendChild(Card({ title:"纸上交易", content:"这里发起 /paper/*（后续实现）" }));
  return box;
}};
