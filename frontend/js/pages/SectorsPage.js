import { Card } from "../components/Card.js";
export default { route: "/sectors", title: "行业轮动", render() {
  const box=document.createElement("div");
  box.appendChild(Card({ title:"行业轮动", content:"这里展示 /sectors/rotation（后续实现）" }));
  return box;
}};
