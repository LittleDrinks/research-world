# React 交互原型

`DeepSeaDesignPrototype.jsx` 是一个 12 变体 UI 原型，按 prototype skill 实现：
- 通过 `?variant=A` ~ `L` 切换；
- 底部浮条左右切换，支持 ← / → 键盘；
- 每个变体是不同结构（布局/信息层级/主操作），不是换色；
- 展示 `Prototype state`，无持久化，纯内存 mock。

挂载示例：
```jsx
<Route path="prototype/deep-sea" element={<DeepSeaDesignPrototype />} />
```
或放入现有页面：
```jsx
if (searchParams.get("prototype") === "deepsea") return <DeepSeaDesignPrototype />;
```
