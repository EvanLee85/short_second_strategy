import { Card } from "../components/Card.js";
export default { route: "/leaders", title: "龙头筛选", render() {
  const box=document.createElement("div");
  box.appendChild(Card({ title:"龙头筛选", content:"这里展示 /stocks/leaders（后续实现）" }));
  return box;
}};
