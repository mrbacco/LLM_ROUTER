let availableModels = []
let bacToolDefaultModel = "gemini-2.0-flash"
let compareDefaultModels = ["gemini-2.0-flash", "gemini-2.0-flash-lite"]

function escapeHtml(text){
return String(text)
  .replaceAll("&","&amp;")
  .replaceAll("<","&lt;")
  .replaceAll(">","&gt;")
  .replaceAll('"',"&quot;")
  .replaceAll("'","&#39;")
}

function renderCompareTable(data){
const rows=Object.entries(data).map(([model,response])=>`
<tr>
<td class="model-cell">${escapeHtml(model)}</td>
<td class="response-cell">${escapeHtml(response ?? "")}</td>
</tr>
`).join("")

return `
<table class="results-table">
<thead>
<tr>
<th>Model</th>
<th>Response</th>
</tr>
</thead>
<tbody>${rows}</tbody>
</table>
`
}

function renderModelSelectors(){
const bacToolSelect=document.getElementById("bacToolModel")
const comparePanel=document.getElementById("compareModels")
const providerCounts={
gemini:2,
groq:5,
openrouter:1,
ollama_cloud:2
}
const providerNames={
gemini:"Gemini",
groq:"Groq",
openrouter:"OpenRouter",
ollama_cloud:"Ollama Cloud"
}
const providerSuffix=(provider)=>{
const count=providerCounts[provider]
const name=providerNames[provider]
if(!count||!name) return ""
return ` (${count} ${name})`
}

if(availableModels.length===0){
bacToolSelect.innerHTML=""
comparePanel.innerHTML="<span>No models available. Add GEMINI_API_KEY, GROQ_API_KEY, or OPENROUTER_API_KEY.</span>"
return
}

bacToolSelect.innerHTML=availableModels.map((model)=>{
const selected=model.id===bacToolDefaultModel ? "selected" : ""
const label=`${model.id}${providerSuffix(model.provider)}`
return `<option value="${escapeHtml(model.id)}" ${selected}>${escapeHtml(label)}</option>`
}).join("")

comparePanel.innerHTML=availableModels.map((model)=>{
const checked=compareDefaultModels.includes(model.id) ? "checked" : ""
const badgeClass=model.type==="remote" ? "badge-remote" : "badge-local"
const label=`${model.id}${providerSuffix(model.provider)}`
return `
<label class="model-choice">
<input type="checkbox" class="compare-model" value="${escapeHtml(model.id)}" ${checked}>
<span>${escapeHtml(label)}</span>
<span class="model-badge ${badgeClass}">${escapeHtml(model.type)}</span>
</label>
`
}).join("")
}

async function loadModels(){
try{
const res=await fetch("/models")
const data=await res.json()
availableModels=data.models||[]
bacToolDefaultModel=data.bac_tool_default||bacToolDefaultModel
compareDefaultModels=data.compare_default||compareDefaultModels
renderModelSelectors()
}catch{
const bacToolSelect=document.getElementById("bacToolModel")
bacToolSelect.innerHTML=`
<option value="gemini-2.0-flash" selected>gemini-2.0-flash</option>
<option value="gemini-2.0-flash-lite">gemini-2.0-flash-lite</option>
`
document.getElementById("compareModels").innerHTML=`
<label class="model-choice"><input type="checkbox" class="compare-model" value="gemini-2.0-flash" checked><span>gemini-2.0-flash</span><span class="model-badge badge-remote">remote</span></label>
<label class="model-choice"><input type="checkbox" class="compare-model" value="gemini-2.0-flash-lite" checked><span>gemini-2.0-flash-lite</span><span class="model-badge badge-remote">remote</span></label>
`
}
}

function selectedCompareModels(){
return [...document.querySelectorAll(".compare-model:checked")].map(el=>el.value)
}

function useFallbackEnabled(){
const toggle=document.getElementById("useFallback")
return toggle ? toggle.checked : true
}

async function runBacTool(){
const msg=document.getElementById("msg").value.trim()
const output=document.getElementById("output")
const model=document.getElementById("bacToolModel").value

if(!msg){
output.textContent="Please enter a message first."
return
}

try{
const res=await fetch("/bac_tool",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({
message:msg,
model:model,
use_fallback:useFallbackEnabled()
})
})

let data
try{
data=await res.json()
}catch{
throw new Error(`Server returned ${res.status} ${res.statusText} and not JSON.`)
}

if(!res.ok){
throw new Error(data.error||`Request failed with status ${res.status}.`)
}

output.innerHTML=`
<table class="results-table">
<thead>
<tr><th>Model</th><th>Response</th></tr>
</thead>
<tbody>
<tr>
<td class="model-cell">${escapeHtml(model)}</td>
<td class="response-cell">${escapeHtml(data.response ?? "")}</td>
</tr>
</tbody>
</table>
`
}catch(err){
output.textContent=`BAC_TOOL failed: ${err.message}`
}
}

async function multipleLlms(){
const output=document.getElementById("output")
const msg=document.getElementById("msg").value.trim()
const models=selectedCompareModels()

if(!msg){
output.textContent="Please enter a message first."
return
}

if(models.length===0){
output.textContent="Please select at least one model for compare."
return
}

try{
const res=await fetch("/compare",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({
message:msg,
models:models,
use_fallback:useFallbackEnabled()
})
})

let data
try{
data=await res.json()
}catch{
throw new Error(`Server returned ${res.status} ${res.statusText} and not JSON.`)
}

if(!res.ok){
throw new Error(data.error||`Request failed with status ${res.status}.`)
}

output.innerHTML=renderCompareTable(data)
}catch(err){
output.textContent=`Compare failed: ${err.message}`
}
}

loadModels()
