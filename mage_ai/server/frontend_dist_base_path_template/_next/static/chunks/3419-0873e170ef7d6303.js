"use strict";(self.webpackChunk_N_E=self.webpackChunk_N_E||[]).push([[3419],{23192:function(n,e,t){t.d(e,{fi:function(){return B},lG:function(){return Y}});var o=t(82394),r=t(75582),i=t(82684),u=t(12691),c=t.n(u),l=t(34376),a=t.n(l),d=t(38626),s=t(69864),p=t(40761),f=t(41143),v=t(71180),b=t(39867),h=t(55485),m=t(48670),j=t(57653),g=t(38276),O=t(75499),x=t(30160),y=t(12468),P=t(35686),Z=t(89706),k=t(11498),_=t(72473),S=t(81655),C=t(70515),w=t(3917),L=t(55283),T=t(86735),D=t(72619),R=t(74052),M=t(69419),I=t(70320),E=t(28598);function N(n,e){var t=Object.keys(n);if(Object.getOwnPropertySymbols){var o=Object.getOwnPropertySymbols(n);e&&(o=o.filter((function(e){return Object.getOwnPropertyDescriptor(n,e).enumerable}))),t.push.apply(t,o)}return t}function A(n){for(var e=1;e<arguments.length;e++){var t=null!=arguments[e]?arguments[e]:{};e%2?N(Object(t),!0).forEach((function(e){(0,o.Z)(n,e,t[e])})):Object.getOwnPropertyDescriptors?Object.defineProperties(n,Object.getOwnPropertyDescriptors(t)):N(Object(t)).forEach((function(e){Object.defineProperty(n,e,Object.getOwnPropertyDescriptor(t,e))}))}return n}var Y=[0,1,3,4,5],B={0:"status",1:"block_uuid",3:"created_at",4:"started_at",5:"completed_at"};e.ZP=function(n){var e=n.blockRuns,t=n.onClickRow,o=n.pipeline,u=n.selectedRun,l=n.setErrors,N=n.sortableColumnIndexes,Y=(0,I.q)(),B=(0,i.useContext)(d.ThemeContext),F=(0,i.useState)(null),U=F[0],X=F[1],H=(0,i.useState)(null),Q=H[0],G=H[1],z=o||{},J=z.uuid,K=z.type,q=(0,i.useMemo)((function(){return o.blocks||[]}),[o]),V=(0,i.useMemo)((function(){return(0,T.HK)(q,(function(n){return n.uuid}))}),[q]),$=(0,i.useMemo)((function(){return j.qL.INTEGRATION===K}),[K]),W=(0,i.useMemo)((function(){return j.qL.PYTHON===K}),[K]),nn=(0,M.iV)(),en=null===nn||void 0===nn?void 0:nn[S.lG.SORT_COL_IDX],tn=(0,i.useMemo)((function(){return en?{columnIndex:+en,sortDirection:(null===nn||void 0===nn?void 0:nn[S.lG.SORT_DIRECTION])||S.sh.ASC}:void 0}),[nn,en]),on=(0,i.useMemo)((function(){var n,e;return null===(n=new p.Z)||void 0===n||null===(e=n.decodedToken)||void 0===e?void 0:e.token}),[]),rn=(0,s.Db)((function(n){var e=n.blockUUID,t=n.pipelineRunId;return P.ZP.block_outputs.pipelines.downloads.detailAsync(null===o||void 0===o?void 0:o.uuid,e,{pipeline_run_id:t,token:on},{onDownloadProgress:function(n){return X((Number((null===n||void 0===n?void 0:n.loaded)||0)/1e6).toFixed(3))},responseType:k.E.BLOB})}),{onSuccess:function(n){return(0,D.wD)(n,{callback:function(n){G(null),(0,R.uS)(n,"block_output.".concat(Z.Lu.CSV))},onErrorCallback:function(n,e){return null===l||void 0===l?void 0:l({errors:e,response:n})}})}}),un=(0,r.Z)(rn,2),cn=un[0],ln=un[1].isLoading,an=Y?S.O$:{},dn=[{uuid:"Status"},{uuid:"Block"},{uuid:"Trigger"},A(A({},an),{},{uuid:"Created at"}),A(A({},an),{},{uuid:"Started at"}),A(A({},an),{},{uuid:"Completed at"}),{uuid:"Logs"}];return W&&dn.push({uuid:"Output"}),(0,E.jsx)(O.Z,{columnFlex:[1,2,2,1,1,1,null,null],columns:dn,isSelectedRow:function(n){return e[n].id===(null===u||void 0===u?void 0:u.id)},onClickRow:t,rows:null===e||void 0===e?void 0:e.map((function(n){var e,t,o,r,u=n||{},l=u.block_uuid,d=u.completed_at,s=u.created_at,p=u.id,j=u.pipeline_run_id,O=u.pipeline_schedule_id,P=u.pipeline_schedule_name,Z=u.started_at,k=u.status,T=l,D=T.split(":"),R=Q===p&&ln;$&&(T=D[0],o=D[1],r=D[2]);var M=V[T];M||(M=V[D[0]]);var I=[(0,i.createElement)(x.ZP,A(A({},(0,S.NC)(k)),{},{key:"".concat(p,"_status")}),k),(0,E.jsx)(c(),{as:"/pipelines/".concat(J,"/edit?block_uuid=").concat(T),href:"/pipelines/[pipeline]/edit",passHref:!0,children:(0,E.jsxs)(m.Z,{bold:!0,fitContentWidth:!0,verticalAlignContent:!0,children:[(0,E.jsx)(b.Z,{color:(0,L.qn)(null===(e=M)||void 0===e?void 0:e.type,{blockColor:null===(t=M)||void 0===t?void 0:t.color,theme:B}).accent,size:1.5*C.iI,square:!0}),(0,E.jsx)(g.Z,{mr:1}),(0,E.jsxs)(x.ZP,{monospace:!0,sky:!0,children:[T,o&&":",o&&(0,E.jsx)(x.ZP,{default:!0,inline:!0,monospace:!0,children:o}),r>=0&&":",r>=0&&(0,E.jsx)(x.ZP,{default:!0,inline:!0,monospace:!0,children:r})]})]})},"".concat(p,"_block_uuid")),(0,E.jsx)(c(),{as:"/pipelines/".concat(J,"/triggers/").concat(O),href:"/pipelines/[pipeline]/triggers/[...slug]",passHref:!0,children:(0,E.jsx)(m.Z,{bold:!0,sky:!0,children:P})},"".concat(p,"_trigger")),(0,E.jsx)(x.ZP,{default:!0,monospace:!0,small:!0,title:s?(0,w._6)(s):null,children:Y?(0,w.XG)(s,Y):(0,w.d$)(s,{includeSeconds:!0})},"".concat(p,"_created_at")),(0,E.jsx)(x.ZP,{default:!0,monospace:!0,small:!0,title:Z?(0,w._6)(Z):null,children:Z?Y?(0,w.XG)(Z,Y):(0,w.d$)(Z,{includeSeconds:!0}):(0,E.jsx)(E.Fragment,{children:"\u2014"})},"".concat(p,"_started_at")),(0,E.jsx)(x.ZP,{default:!0,monospace:!0,small:!0,title:d?(0,w._6)(d):null,children:d?Y?(0,w.XG)(d,Y):(0,w.d$)(d,{includeSeconds:!0}):(0,E.jsx)(E.Fragment,{children:"\u2014"})},"".concat(p,"_completed_at")),(0,E.jsx)(v.ZP,{default:!0,iconOnly:!0,noBackground:!0,onClick:function(){return a().push("/pipelines/".concat(J,"/logs?block_run_id[]=").concat(p))},children:(0,E.jsx)(_.UL,{default:!0,size:2*C.iI})},"".concat(p,"_logs"))];return W&&I.push((0,E.jsx)(h.ZP,{alignItems:"center",justifyContent:"center",children:(0,E.jsx)(y.Z,{appearBefore:!0,autoHide:!R,block:!0,forceVisible:R,label:R?"".concat(U||0,"mb downloaded..."):"Save block run output as CSV file (not supported for dynamic blocks)",size:null,children:(0,E.jsx)(v.ZP,{default:!0,disabled:!W||!(f.V.COMPLETED===k)||ln,iconOnly:!0,loading:R,noBackground:!0,onClick:function(){X(null),G(p),cn({blockUUID:T,pipelineRunId:j})},children:(0,E.jsx)(_.vc,{default:!0,size:2*C.iI})})})},"".concat(p,"_save_output"))),I})),sortableColumnIndexes:N,sortedColumn:tn,uuid:"block-runs"})}},74052:function(n,e,t){t.d(e,{Dp:function(){return h},OF:function(){return m},Q9:function(){return g},Rt:function(){return f},Rz:function(){return x},h8:function(){return j},k1:function(){return v},uS:function(){return O},zv:function(){return y}});var o=t(21831),r=t(82394),i=t(48339),u=t(53808),c=t(3917),l=t(86735),a=t(81728),d=t(70320);function s(n,e){var t=Object.keys(n);if(Object.getOwnPropertySymbols){var o=Object.getOwnPropertySymbols(n);e&&(o=o.filter((function(e){return Object.getOwnPropertyDescriptor(n,e).enumerable}))),t.push.apply(t,o)}return t}function p(n){for(var e=1;e<arguments.length;e++){var t=null!=arguments[e]?arguments[e]:{};e%2?s(Object(t),!0).forEach((function(e){(0,r.Z)(n,e,t[e])})):Object.getOwnPropertyDescriptors?Object.defineProperties(n,Object.getOwnPropertyDescriptors(t)):s(Object(t)).forEach((function(e){Object.defineProperty(n,e,Object.getOwnPropertyDescriptor(t,e))}))}return n}function f(n){var e={},t={};return null===n||void 0===n||n.forEach((function(n){var o=n.content,r=n.outputs,u=n.type,c=n.uuid;(null===r||void 0===r?void 0:r.length)>=1&&(e[c]=r.map((function(n){if("object"===typeof n){var e=n||{},t=e.sample_data,o=e.shape,r=e.text_data,u=e.type;return t?{data:p({shape:o},t),type:u}:r&&(0,a.Pb)(r)?JSON.parse(r):r}return{data:String(n),type:i.Gi.TEXT}}))),t[u]||(t[u]={}),t[u][c]=o})),{content:t,messages:e}}function v(n,e,t){n.forEach((function(n){(0,u.t8)("".concat(t,"/").concat(n.uuid,"/codeCollapsed"),(0,u.Od)("".concat(e,"/").concat(n.uuid,"/codeCollapsed"))),(0,u.t8)("".concat(t,"/").concat(n.uuid,"/outputCollapsed"),(0,u.Od)("".concat(e,"/").concat(n.uuid,"/outputCollapsed")))}))}function b(n){return"".concat(n,"/").concat(u.kP)}function h(n){return(0,u.U2)(b(n),[])}function m(n,e){var t=h(n);t.includes(e)||(0,u.t8)(b(n),[].concat((0,o.Z)(t),[e]))}function j(n,e){var t=h(n).filter((function(n){return n!==e}));(0,u.t8)(b(n),t)}function g(n,e){var t=(0,l.HK)(e,(function(n){return n.uuid}));return n.map((function(n){return t[n]})).filter((function(n){return!!n}))}var O=function(n,e){var t=window.URL.createObjectURL(n),o=document.createElement("a");o.href=t,o.download=e,document.body.appendChild(o),o.click(),o.remove()};function x(n,e){var t,o=(0,d.q)(),r=null===e||void 0===e?void 0:e.isPipelineUpdating,i=null===e||void 0===e?void 0:e.pipelineContentTouched,u=null===e||void 0===e?void 0:e.pipelineLastSaved;if(i)t="Unsaved changes";else if(r)t="Saving changes...";else if(u){var l=(0,c.JX)(Number(u)/1e3);null!==n&&void 0!==n&&n.updated_at&&(l=(0,c.XG)(null===n||void 0===n?void 0:n.updated_at,o)),t="Last saved ".concat(l)}else t="All changes saved";return t}function y(n){var e=n.type,t=n.uuid;return"".concat(e,"s/").concat(t,".py")}},8955:function(n,e,t){t.d(e,{G7:function(){return y},ZP:function(){return P},u$:function(){return g}});var o=t(75582),r=t(82394),i=t(26304),u=t(90299),c=t(9134),l=t(24138),a=t(38276),d=t(30160),s=t(75499),p=t(70515),f=t(16488),v=t(42122),b=t(28598),h=["height","heightOffset","pipeline","selectedRun","selectedTab","setSelectedTab"];function m(n,e){var t=Object.keys(n);if(Object.getOwnPropertySymbols){var o=Object.getOwnPropertySymbols(n);e&&(o=o.filter((function(e){return Object.getOwnPropertyDescriptor(n,e).enumerable}))),t.push.apply(t,o)}return t}function j(n){for(var e=1;e<arguments.length;e++){var t=null!=arguments[e]?arguments[e]:{};e%2?m(Object(t),!0).forEach((function(e){(0,r.Z)(n,e,t[e])})):Object.getOwnPropertyDescriptors?Object.defineProperties(n,Object.getOwnPropertyDescriptors(t)):m(Object(t)).forEach((function(e){Object.defineProperty(n,e,Object.getOwnPropertyDescriptor(t,e))}))}return n}var g=76,O={uuid:"Run details"},x={uuid:"Dependency tree"},y=[x,O];function P(n){var e=n.height,t=n.heightOffset,r=n.pipeline,m=n.selectedRun,P=n.selectedTab,Z=n.setSelectedTab,k=j({},(0,i.Z)(n,h));m?k.blockStatus=(0,f.IJ)(null===m||void 0===m?void 0:m.block_runs):k.noStatus=!0;var _=(0,v.Kn)(null===m||void 0===m?void 0:m.variables)?j({},null===m||void 0===m?void 0:m.variables):(null===m||void 0===m?void 0:m.variables)||{},S=null===m||void 0===m?void 0:m.event_variables;if(S&&(0,v.Kn)(S)&&!(0,v.Qr)(S))if((0,v.Kn)(_)&&_.hasOwnProperty("event")){var C=(0,v.Kn)(_.event)?_.event:{};_.event=j(j({},C),S)}else _.event=j({},S);var w=[];_&&JSON.stringify(_,null,2).split("\n").forEach((function(n){w.push("    ".concat(n))}));var L=m&&[["Run ID",null===m||void 0===m?void 0:m.id],["Variables",(0,b.jsx)(c.Z,{language:"json",small:!0,source:w.join("\n")},"variable_value")]],T=m&&(0,b.jsx)(a.Z,{pb:p.cd,px:p.cd,children:(0,b.jsx)(s.Z,{alignTop:!0,columnFlex:[null,1],columnMaxWidth:function(n){return 1===n?"100px":null},rows:L.map((function(n,e){var t=(0,o.Z)(n,2),r=t[0],i=t[1];return[(0,b.jsx)(d.ZP,{monospace:!0,muted:!0,children:r},"key_".concat(e)),(0,b.jsx)(d.ZP,{monospace:!0,textOverflow:!0,children:i},"val_".concat(e))]})),uuid:"LogDetail"})}),D=P&&Z;return(0,b.jsxs)(b.Fragment,{children:[D&&(0,b.jsx)(a.Z,{py:p.cd,children:(0,b.jsx)(u.Z,{onClickTab:Z,selectedTabUUID:null===P||void 0===P?void 0:P.uuid,tabs:y})}),(!D||x.uuid===(null===P||void 0===P?void 0:P.uuid))&&(0,b.jsx)(l.ZP,j(j({},k),{},{height:e,heightOffset:(t||0)+(D?g:0),pipeline:r})),O.uuid===(null===P||void 0===P?void 0:P.uuid)&&T]})}},55072:function(n,e,t){t.d(e,{Et:function(){return p},Q:function(){return s}});t(82684);var o=t(71180),r=t(55485),i=t(38276),u=t(31748),c=t(72473),l=t(79633),a=t(70515),d=t(28598),s=30,p=9;e.ZP=function(n){var e=n.page,t=n.maxPages,s=n.onUpdate,p=n.totalPages,f=[],v=t;if(v>p)f=Array.from({length:p},(function(n,e){return e}));else{var b=Math.floor(v/2),h=e-b;e+b>=p?(h=p-v+2,v-=2):e-b<=0?(h=0,v-=2):(v-=4,h=e-Math.floor(v/2)),f=Array.from({length:v},(function(n,e){return e+h}))}return(0,d.jsx)(d.Fragment,{children:p>0&&(0,d.jsxs)(r.ZP,{alignItems:"center",children:[(0,d.jsx)(o.ZP,{disabled:0===e,onClick:function(){return s(e-1)},children:(0,d.jsx)(c.Hd,{size:1.5*a.iI,stroke:u.Av})}),!f.includes(0)&&(0,d.jsxs)(d.Fragment,{children:[(0,d.jsx)(i.Z,{ml:1,children:(0,d.jsx)(o.ZP,{borderLess:!0,noBackground:!0,onClick:function(){return s(0)},children:1})},0),!f.includes(1)&&(0,d.jsx)(i.Z,{ml:1,children:(0,d.jsx)(o.ZP,{noBackground:!0,noPadding:!0,notClickable:!0,children:"..."})},0)]}),f.map((function(n){return(0,d.jsx)(i.Z,{ml:1,children:(0,d.jsx)(o.ZP,{backgroundColor:n===e&&l.a$,borderLess:!0,noBackground:!0,notClickable:n===e,onClick:function(){n!==e&&s(n)},children:n+1})},n)})),!f.includes(p-1)&&(0,d.jsxs)(d.Fragment,{children:[!f.includes(p-2)&&(0,d.jsx)(i.Z,{ml:1,children:(0,d.jsx)(o.ZP,{noBackground:!0,noPadding:!0,notClickable:!0,children:"..."})},0),(0,d.jsx)(i.Z,{ml:1,children:(0,d.jsx)(o.ZP,{borderLess:!0,noBackground:!0,onClick:function(){return s(p-1)},children:p})},p-1)]}),(0,d.jsx)(i.Z,{ml:1}),(0,d.jsx)(o.ZP,{disabled:e===p-1,onClick:function(){return s(e+1)},children:(0,d.jsx)(c.Kw,{size:1.5*a.iI,stroke:u.Av})})]})})}},89706:function(n,e,t){t.d(e,{JD:function(){return b},Lu:function(){return i},PF:function(){return p},dT:function(){return u},n6:function(){return a},nB:function(){return v},oy:function(){return f},xF:function(){return s}});var o,r,i,u,c=t(82394),l=t(44425);!function(n){n.CSV="csv",n.JSON="json",n.MD="md",n.PY="py",n.R="r",n.SH="sh",n.SQL="sql",n.TXT="txt",n.YAML="yaml",n.YML="yml"}(i||(i={})),function(n){n.INIT_PY="__init__.py",n.METADATA_YAML="metadata.yaml",n.REQS_TXT="requirements.txt"}(u||(u={}));var a=[i.PY,i.SQL],d=[i.JSON,i.MD,i.PY,i.R,i.SH,i.SQL,i.TXT,i.YAML,i.YML],s=new RegExp(d.map((function(n){return".".concat(n,"$")})).join("|")),p=(new RegExp(d.map((function(n){return".".concat(n,"$")})).join("|")),"charts"),f="pipelines",v=(o={},(0,c.Z)(o,i.MD,l.t6.MARKDOWN),(0,c.Z)(o,i.JSON,i.JSON),(0,c.Z)(o,i.PY,l.t6.PYTHON),(0,c.Z)(o,i.R,l.t6.R),(0,c.Z)(o,i.SQL,l.t6.SQL),(0,c.Z)(o,i.TXT,"text"),(0,c.Z)(o,i.YAML,l.t6.YAML),(0,c.Z)(o,i.YML,l.t6.YAML),o),b=(r={},(0,c.Z)(r,l.t6.MARKDOWN,i.MD),(0,c.Z)(r,l.t6.PYTHON,i.PY),(0,c.Z)(r,l.t6.R,i.R),(0,c.Z)(r,l.t6.SQL,i.SQL),(0,c.Z)(r,l.t6.YAML,i.YAML),(0,c.Z)(r,"text",i.TXT),r)},9134:function(n,e,t){var o=t(82684),r=t(21124),i=t(68432),u=t(38626),c=t(65292),l=t(44897),a=t(95363),d=t(70515),s=t(28598);e.Z=function(n){var e=n.language,t=n.maxWidth,p=n.showLineNumbers,f=n.small,v=n.source,b=n.wrapLines,h=(0,o.useContext)(u.ThemeContext);function m(n){var o=n.value;return(0,s.jsx)(i.Z,{customStyle:{backgroundColor:(h.background||l.Z.background).popup,border:"none",borderRadius:"none",boxShadow:"none",fontFamily:a.Vp,fontSize:f?12:14,marginBottom:0,marginTop:0,maxWidth:t,paddingBottom:2*d.iI,paddingTop:2*d.iI},language:e,lineNumberStyle:{color:(h.content||l.Z.content).muted},showLineNumbers:p,style:c._4,useInlineStyles:!0,wrapLines:b,children:o})}return(0,s.jsx)(r.D,{components:{code:function(n){var e=n.children;return(0,s.jsx)(m,{value:e})}},children:v})}}}]);