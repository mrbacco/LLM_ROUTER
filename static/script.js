let availableModels = []
let bacToolDefaultModel = "gemini-2.0-flash"
let compareDefaultModels = ["gemini-2.0-flash", "gemini-2.0-flash-lite"]
let runMode = "single"
const DEFAULT_UPLOAD_STATUS = "Optional: choose files/images from the + menu, then send."

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
const modelSuffix=(modelId)=>{
const id=String(modelId||"").toLowerCase()
const tags=[]
if(id.includes(":free")) tags.push("free")
if(id.includes("gpt-oss")||id.includes("llama")||id.includes("gemma")) tags.push("open-source")
if(tags.length===0) return ""
return ` (${tags.join(", ")})`
}

if(availableModels.length===0){
bacToolSelect.innerHTML=""
comparePanel.innerHTML="<span>No models available. Add CLOUDFLARE_API_TOKEN+CLOUDFLARE_ACCOUNT_ID, GEMINI_API_KEY, OPENROUTER_API_KEY, or OLLAMA_API_KEY.</span>"
return
}

bacToolSelect.innerHTML=availableModels.map((model)=>{
const selected=model.id===bacToolDefaultModel ? "selected" : ""
const label=`${model.id}${modelSuffix(model.id)}`
return `<option value="${escapeHtml(model.id)}" ${selected}>${escapeHtml(label)}</option>`
}).join("")

comparePanel.innerHTML=availableModels.map((model)=>{
const checked=compareDefaultModels.includes(model.id) ? "checked" : ""
const badgeClass=model.type==="remote" ? "badge-remote" : "badge-local"
const label=`${model.id}${modelSuffix(model.id)}`
return `
<label class="model-choice">
<input type="checkbox" class="compare-model" value="${escapeHtml(model.id)}" ${checked}>
<span>${escapeHtml(label)}</span>
<span class="model-badge ${badgeClass}">${escapeHtml(model.type)}</span>
</label>
`
}).join("")
renderHealthModelSelector()
renderModeSummary()
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
availableModels=[
{id:"gemini-2.0-flash",provider:"gemini",type:"remote"},
{id:"gemini-2.0-flash-lite",provider:"gemini",type:"remote"}
]
renderHealthModelSelector()
}
}

function selectedCompareModels(){
return [...document.querySelectorAll(".compare-model:checked")].map(el=>el.value)
}

function useFallbackEnabled(){
const toggle=document.getElementById("useFallback")
return toggle ? toggle.checked : true
}

function currentAttachedFiles(){
const fileInput=document.getElementById("file")
return fileInput && fileInput.files ? [...fileInput.files] : []
}

function renderFileChips(){
const container=document.getElementById("fileChips")
if(!container) return
const files=currentAttachedFiles()
if(files.length===0){
container.innerHTML=""
return
}
container.innerHTML=files.map((f)=>`<span class="file-chip">${escapeHtml(f.name)}</span>`).join("")
}

function setOutputVisibility(show){
const wrap=document.querySelector(".output-wrap")
if(wrap){
wrap.classList.toggle("hidden",!show)
}
}

function setRequestStatus(isLoading,message){
const status=document.getElementById("requestStatus")
if(!status) return
if(!isLoading){
status.classList.add("hidden")
status.innerHTML=""
return
}
const label=escapeHtml(message||"Contacting model")
status.innerHTML=`${label}<span class="dots"><span></span><span></span><span></span></span>`
status.classList.remove("hidden")
}

function submitPrompt(){
if(runMode==="multiple"){
multipleLlms()
return
}
runBacTool()
}

function applyModeVisibility(){
const singlePanel=document.getElementById("singleModelPanel")
const multiplePanel=document.getElementById("multipleModelPanel")
if(singlePanel) singlePanel.classList.toggle("hidden",runMode!=="single")
if(multiplePanel) multiplePanel.classList.toggle("hidden",runMode!=="multiple")
}

function renderModeSummary(){
const summary=document.getElementById("modeSummary")
if(!summary) return
if(runMode==="multiple"){
const count=selectedCompareModels().length
summary.textContent=`Multiple models (${count} selected)`
return
}
const model=document.getElementById("bacToolModel")
const value=model ? model.value : ""
summary.textContent=value ? `Single model (${value})` : "Single model"
}

function toggleRunMode(){
const modeToggle=document.getElementById("modeMultipleEnabled")
runMode=(modeToggle && modeToggle.checked) ? "multiple" : "single"
applyModeVisibility()
renderModeSummary()
}

function hideToolsMenu(){
const menu=document.getElementById("toolsMenu")
if(menu) menu.classList.add("hidden")
}

function toggleToolsMenu(){
const menu=document.getElementById("toolsMenu")
if(!menu) return
menu.classList.toggle("hidden")
}

function onSelectAddFiles(){
hideToolsMenu()
const fileInput=document.getElementById("file")
if(fileInput) fileInput.click()
}

function renderDocumentsInfo(data){
const target=document.getElementById("documentsInfo")
if(!target) return
const docs=(data&&data.documents)||[]
if(docs.length===0){
target.textContent="No indexed documents yet."
return
}

function resetUploadStatus(){
const status=document.getElementById("uploadStatus")
if(status){
status.textContent=DEFAULT_UPLOAD_STATUS
}
}
const names=docs.slice(0,5).map((d)=>`${d.name} (${d.chunk_count} chunks)`).join(" | ")
const extra=docs.length>5 ? ` | +${docs.length-5} more` : ""
target.textContent=`Indexed documents: ${docs.length}. ${names}${extra}`
}

function healthDetailText(item){
const detail=String(item.detail||"")
if(detail.length<=92) return detail
return `${detail.slice(0,92)}...`
}

function healthEnabled(){
const checkbox=document.getElementById("healthEnabled")
return checkbox ? checkbox.checked : true
}

function toggleHealthBox(){
const enabled=healthEnabled()
const box=document.getElementById("healthBox")
if(box){
box.classList.toggle("hidden",!enabled)
}
try{
localStorage.setItem("health_enabled",enabled ? "1" : "0")
}catch{
}
}

function initHealthToggle(){
const checkbox=document.getElementById("healthEnabled")
if(!checkbox) return
checkbox.checked=false
try{
localStorage.setItem("health_enabled","0")
}catch{
}
toggleHealthBox()
}

function renderHealthModelSelector(){
const target=document.getElementById("healthModelSelector")
if(!target) return
if(!availableModels || availableModels.length===0){
target.innerHTML="<div class='health-empty'>No models available.</div>"
return
}
target.innerHTML=availableModels.map((model)=>{
return `
<label class="health-select-item">
<input type="checkbox" class="health-model-check" value="${escapeHtml(model.id)}" checked>
<span>${escapeHtml(model.id)}</span>
</label>
`
}).join("")
}

function selectedHealthModels(){
return [...document.querySelectorAll(".health-model-check:checked")].map((el)=>el.value)
}

function renderModelHealth(data){
const target=document.getElementById("modelHealth")
if(!target) return
const rows=(data&&data.results)||[]
if(rows.length===0){
target.innerHTML="<div class='health-empty'>No configured models.</div>"
return
}
target.innerHTML=rows.map((item)=>{
const ok=item.status==="working"
return `
<div class="health-row">
<span class="health-model">${escapeHtml(item.model)}</span>
<span class="health-badge ${ok ? "ok" : "fail"}">${ok ? "working" : "failing"}</span>
<div class="health-detail">${escapeHtml(healthDetailText(item))}</div>
</div>
`
}).join("")
}

async function loadModelHealth(force=false){
if(!healthEnabled()) return
const target=document.getElementById("modelHealth")
const btn=document.getElementById("healthCheckBtn")
if(target && force){
target.innerHTML="<div class='health-loading'>Checking health<span class='dots'><span></span><span></span><span></span></span></div>"
}
const models=selectedHealthModels()
if(models.length===0){
if(target) target.innerHTML="<div class='health-empty'>Select at least one model.</div>"
return
}
if(btn) btn.disabled=true
try{
const res=await fetch("/health/models",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({models})
})
if(!res.ok){
throw new Error(`Health check failed: ${res.status}`)
}
const data=await res.json()
renderModelHealth(data)
}catch(err){
if(target){
target.innerHTML=`<div class='health-empty'>Health check failed: ${escapeHtml(err.message)}</div>`
}
}finally{
if(btn) btn.disabled=false
}
}

function checkSelectedHealth(){
loadModelHealth(true)
}

async function loadDocuments(){
try{
const res=await fetch("/documents")
if(!res.ok) return
const data=await res.json()
renderDocumentsInfo(data)
}catch{
}
}

async function uploadFilesForPrompt(files){
const status=document.getElementById("uploadStatus")
const uploadedIds=[]
let imageCount=0
if(!files||files.length===0){
return uploadedIds
}

for(let i=0;i<files.length;i++){
const file=files[i]
const formData=new FormData()
formData.append("file",file)
status.textContent=`Uploading and indexing ${file.name} (${i+1}/${files.length})...`

const res=await fetch("/upload",{method:"POST",body:formData})
let data
try{
data=await res.json()
}catch{
throw new Error(`Upload returned ${res.status} ${res.statusText} and not JSON.`)
}
if(!res.ok){
throw new Error(data.error||`Upload failed with status ${res.status}.`)
}
const doc=data.document||{}
if(doc.file_id){
uploadedIds.push(doc.file_id)
}
if(doc.kind==="image"){
imageCount+=1
}
}

status.textContent=`Attached ${files.length} file(s) for this request (${uploadedIds.length} text-indexed${imageCount ? `, ${imageCount} image` : ""}).`
await loadDocuments()
return uploadedIds
}

function setLoadingState(isLoading,output,message){
const buttons=[...document.querySelectorAll("button")]
buttons.forEach((btn)=>{btn.disabled=isLoading})
if(isLoading){
output.textContent=message||"Fetching information from backend..."
}
setRequestStatus(isLoading,message)
}

async function runBacTool(){
const msg=document.getElementById("msg").value.trim()
const output=document.getElementById("output")
const model=document.getElementById("bacToolModel").value
const fileInput=document.getElementById("file")
const attachedFiles=currentAttachedFiles()

if(!msg){
output.textContent="Please enter a message first."
setOutputVisibility(true)
return
}

setOutputVisibility(false)
setLoadingState(true,output,"Contacting selected model")

try{
const fileIds=await uploadFilesForPrompt(attachedFiles)
const res=await fetch("/bac_tool",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({
message:msg,
model:model,
use_fallback:useFallbackEnabled(),
file_ids:fileIds
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
<td class="response-cell">${escapeHtml(data.response ?? "")}
${typeof data.rag_hits==="number" ? `\n\n[Grounded with ${data.rag_hits} document snippet(s)]` : ""}
</td>
</tr>
</tbody>
</table>
`
setOutputVisibility(true)
if(fileInput){
fileInput.value=""
renderFileChips()
}
}catch(err){
output.textContent=`BAC_TOOL failed: ${err.message}`
setOutputVisibility(true)
}finally{
setLoadingState(false,output)
resetUploadStatus()
}
}

async function multipleLlms(){
const output=document.getElementById("output")
const msg=document.getElementById("msg").value.trim()
const models=selectedCompareModels()
const fileInput=document.getElementById("file")
const attachedFiles=currentAttachedFiles()

if(!msg){
output.textContent="Please enter a message first."
setOutputVisibility(true)
return
}

if(models.length===0){
output.textContent="Please select at least one model for compare."
setOutputVisibility(true)
return
}

setOutputVisibility(false)
setLoadingState(true,output,"Contacting selected models")

try{
const fileIds=await uploadFilesForPrompt(attachedFiles)
const res=await fetch("/compare",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({
message:msg,
models:models,
use_fallback:useFallbackEnabled(),
file_ids:fileIds
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
setOutputVisibility(true)
if(fileInput){
fileInput.value=""
renderFileChips()
}
}catch(err){
output.textContent=`Compare failed: ${err.message}`
setOutputVisibility(true)
}finally{
setLoadingState(false,output)
resetUploadStatus()
}
}

loadModels()
loadDocuments()
initHealthToggle()
toggleRunMode()
applyModeVisibility()
setOutputVisibility(false)
renderFileChips()
renderModeSummary()

const fileInput=document.getElementById("file")
if(fileInput){
fileInput.addEventListener("change",()=>{
renderFileChips()
hideToolsMenu()
const status=document.getElementById("uploadStatus")
const files=currentAttachedFiles()
if(status){
if(files.length===0){
status.textContent="No files selected."
}else{
status.textContent=`Selected ${files.length} file(s). Click Send to upload and run.`
}
}
})
}

const singleModelSelect=document.getElementById("bacToolModel")
if(singleModelSelect){
singleModelSelect.addEventListener("change",renderModeSummary)
}

const comparePanel=document.getElementById("compareModels")
if(comparePanel){
comparePanel.addEventListener("change",renderModeSummary)
}

document.addEventListener("click",(event)=>{
const toolsMenu=document.getElementById("toolsMenu")
const toolsBtn=document.getElementById("toolsBtn")
if(toolsMenu && toolsBtn){
const inMenu=toolsMenu.contains(event.target)
const inBtn=toolsBtn.contains(event.target)
if(!inMenu && !inBtn) toolsMenu.classList.add("hidden")
}

})

const msgInput=document.getElementById("msg")
if(msgInput){
msgInput.addEventListener("keydown",(event)=>{
if(event.key==="Enter" && !event.shiftKey){
event.preventDefault()
submitPrompt()
}
})
}
