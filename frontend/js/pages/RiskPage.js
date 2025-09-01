import { Card } from "../components/Card.js";
export default { route: "/risk", title: "风控评估", render() {
  const box=document.createElement("div");
  box.appendChild(Card({ title:"风控评估", content:"这里发起 /risk/*（后续实现）" }));
  return box;
}};
