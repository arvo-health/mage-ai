(self.webpackChunk_N_E=self.webpackChunk_N_E||[]).push([[8662],{62976:function(e,n,t){"use strict";t.d(n,{Z:function(){return R}});var r=t(82394),i=t(77555),o=t(82684),u=t(10919),l=t(12691),c=t.n(l),a=t(34376),d=t.n(a),s=t(9518),p=t(63068),f=t(44628),h=t(6508),m=t(67971),v=t(19711),g=t(23831),b=t(31969),y=function(){var e=document.createElement("div");e.setAttribute("style","width: 100px; height: 100px; overflow: scroll; position:absolute; top:-9999px;"),document.body.appendChild(e);var n=e.offsetWidth-e.clientWidth;return document.body.removeChild(e),n},x=t(2005),O=t(31012),j=t(37391),w=t(6753),Z=t(49125),P=t(69345),E=t(24224),k=t(28598);function _(e,n){var t=Object.keys(e);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(e);n&&(r=r.filter((function(n){return Object.getOwnPropertyDescriptor(e,n).enumerable}))),t.push.apply(t,r)}return t}function S(e){for(var n=1;n<arguments.length;n++){var t=null!=arguments[n]?arguments[n]:{};n%2?_(Object(t),!0).forEach((function(n){(0,r.Z)(e,n,t[n])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(t)):_(Object(t)).forEach((function(n){Object.defineProperty(e,n,Object.getOwnPropertyDescriptor(t,n))}))}return e}var D=2*Z.iI+O.dN,I=20*Z.iI,C=s.default.div.withConfig({displayName:"DataTable__Styles",componentId:"sc-1arr863-0"})([""," "," "," .body > div{","}.table{border-spacing:0;display:inline-block;"," "," "," "," .tr{.td.td-index-column{","}}.th{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;","}.th,.td{"," font-family:",";margin:0;","}.td{padding:","px;}&.sticky{overflow:auto;}.header{overflow:hidden;}}"],(function(e){return e.disableScrolling&&"\n    overflow: hidden;\n  "}),(function(e){return e.height&&"\n    height: ".concat(e.height,"px;\n  ")}),(function(e){return e.maxHeight&&"\n    max-height: ".concat(e.maxHeight,"px;\n  ")}),j.w5,(function(e){return!e.noBorderBottom&&"\n      border-bottom: 1px solid ".concat((e.theme.borders||b.Z.borders).medium,";\n    ")}),(function(e){return!e.noBorderLeft&&"\n      border-left: 1px solid ".concat((e.theme.borders||b.Z.borders).medium,";\n    ")}),(function(e){return!e.noBorderRight&&"\n      border-right: 1px solid ".concat((e.theme.borders||b.Z.borders).medium,";\n    ")}),(function(e){return!e.noBorderTop&&"\n      border-top: 1px solid ".concat((e.theme.borders||b.Z.borders).medium,";\n    ")}),(function(e){return"\n          color: ".concat((e.theme.content||b.Z.content).default,";\n        ")}),(function(e){return"\n        height: ".concat(e.columnHeaderHeight||D,"px;\n      ")}),O.iD,x.ry,(function(e){return"\n        background-color: ".concat((e.theme.background||b.Z.background).table,";\n        border-bottom: 1px solid ").concat((e.theme.borders||b.Z.borders).medium,";\n        border-right: 1px solid ").concat((e.theme.borders||b.Z.borders).medium,";\n      ")}),1*Z.iI);function T(e){var n=e.original,t=8.5*Math.max.apply(Math,(0,i.Z)(n.map((function(e){return(null===e||void 0===e?void 0:e.length)||0})))),r=Math.ceil(t/(I-2*Z.iI));return Math.max(r,1)*O.dN+2*Z.iI}function N(e){var n=e.columnHeaderHeight,t=e.columns,r=e.data,l=e.disableScrolling,a=e.height,j=e.index,_=e.invalidValues,C=e.maxHeight,N=e.numberOfIndexes,R=e.previewIndexes,H=e.renderColumnHeader,M=e.width,A=(0,o.useContext)(s.ThemeContext),B=(0,o.useRef)(null),L=(0,o.useRef)(null);(0,o.useEffect)((function(){var e=function(e){var n;null===B||void 0===B||null===(n=B.current)||void 0===n||n.scroll(e.target.scrollLeft,0)};return L&&L.current.addEventListener("scroll",e),function(){var n;null===L||void 0===L||null===(n=L.current)||void 0===n||n.removeEventListener("scroll",e)}}),[B,L]);var U=(0,o.useMemo)((function(){return j&&r&&j.length===r.length}),[r,j]),V=(0,o.useMemo)((function(){var e=[];return(0,E.w6)(N).forEach((function(n,t){var o=8.7*String(null===r||void 0===r?void 0:r.length).length;if(U){var u=j.map((function(e){return N>=2?String(e[t]).length:String(e).length}));o=8.7*Math.max.apply(Math,(0,i.Z)(u))}e.push(o+2*Z.iI)})),e}),[r,j,N,U]),F=t.map((function(e){return null===e||void 0===e?void 0:e.Header})).slice(1),G=(0,o.useMemo)((function(){return y()}),[]),X=(0,o.useMemo)((function(){var e=M-(Math.max.apply(Math,(0,i.Z)(V))+1.5*Z.iI+G),n=t.length-1,r=I;return r*n<e&&(r=e/n),{width:r}}),[t,V,G,M]),W=(0,f.useTable)({columns:t,data:r,defaultColumn:X},f.useBlockLayout,h.useSticky),q=W.getTableBodyProps,J=W.getTableProps,Y=W.headerGroups,z=W.prepareRow,K=W.rows,Q=d().query.slug,$=void 0===Q?[]:Q,ee=new Set((null===R||void 0===R?void 0:R.removedRows)||[]),ne=(0,o.useCallback)((function(e){var n=e.index,t=e.style,r=K[n];z(r);var i=r.original,l=ee.has(n);return(0,k.jsx)("div",S(S({},r.getRowProps({style:S(S({},t),{},{width:"auto"})})),{},{className:"tr",children:r.cells.map((function(e,t){var r,a=t<=N-1,d=e.getCellProps(),s=e.column.id,p=null===_||void 0===_||null===(r=_[s])||void 0===r?void 0:r.includes(n),f=S({},d.style);a&&(f.fontFamily=x.Vp,f.left=0,f.position="sticky",f.textAlign=j?"right":"center",f.width=V[t]);var h,g=i[t-N],y=F.indexOf(s);if(p&&(f.color=b.Z.interactive.dangerBorder),l&&(f.backgroundColor=b.Z.background.danger),Array.isArray(g)||"object"===typeof g)try{g=JSON.stringify(g)}catch(O){g="Error: cannot display value"}return a&&(U?(h=j[n],Array.isArray(h)&&(h=h[t])):h=e.render("Cell")),(0,o.createElement)("div",S(S({},d),{},{className:"td ".concat(a?"td-index-column":""),key:"".concat(t,"-").concat(g),style:f}),h,!a&&(0,k.jsxs)(m.Z,{justifyContent:"space-between",children:[(0,k.jsxs)(v.ZP,{danger:p,default:!0,wordBreak:!0,children:[!0===g&&"true",!1===g&&"false",(null===g||"null"===g)&&"null",!0!==g&&!1!==g&&null!==g&&"null"!==g&&g]}),p&&(0,k.jsx)(c(),{as:(0,P.o_)(w.mW,y),href:"/datasets/[...slug]",passHref:!0,children:(0,k.jsx)(u.Z,{danger:!0,children:"View all"})})]}))}))}))}),[j,_,V,N,z,K,$]),te=(0,o.useMemo)((function(){var e;return C?(e=(0,E.Sm)(K.map(T)),e+=n||D-O.dN):(e=a,e-=n||D),e}),[n,T,a,C,K]),re=(0,o.useMemo)((function(){return(0,k.jsx)(p.S_,{estimatedItemSize:D,height:te,itemCount:null===K||void 0===K?void 0:K.length,itemSize:function(e){return T(K[e])},outerRef:L,style:{maxHeight:C,pointerEvents:l?"none":null},children:ne})}),[te,L,ne,K]);return(0,k.jsx)("div",S(S({},J()),{},{className:"table sticky",style:{width:M},children:(0,k.jsxs)("div",S(S({},q()),{},{className:"body",children:[(0,k.jsx)("div",{className:"header",ref:B,children:Y.map((function(e,n){return(0,o.createElement)("div",S(S({},e.getHeaderGroupProps()),{},{className:"tr",key:"".concat(e.id,"_").concat(n)}),e.headers.map((function(e,n){var t,r=n<=N-1,i=e.getHeaderProps(),u=S({},i.style);return r?(u.fontFamily=x.Vp,u.left=0,u.position="sticky",u.textAlign="center",u.width=V[n],u.minWidth=V[n]):H?t=H(e,n-N,{width:X.width}):(t=e.render("Header"),u.color=(A||g.Z).content.default,u.padding=1*Z.iI,u.minWidth=X.width),(0,o.createElement)("div",S(S({},i),{},{className:"th",key:e.id,style:u,title:r?"Row number":void 0}),t)})))}))}),re]}))}))}var R=function(e){var n=e.columnHeaderHeight,t=e.columns,i=e.disableScrolling,u=e.height,l=e.index,c=e.invalidValues,a=e.maxHeight,d=e.noBorderBottom,s=e.noBorderLeft,p=e.noBorderRight,f=e.noBorderTop,h=e.previewIndexes,m=e.renderColumnHeader,v=e.rows,g=e.width,b=(0,o.useMemo)((function(){return null!==l&&void 0!==l&&l.length&&Array.isArray(l[0])?l[0].length:1}),[l]),y=(0,o.useMemo)((function(){return(0,E.w6)(b).map((function(e,n){return{Header:(0,E.w6)(n+1).map((function(){return" "})).join(" "),accessor:function(e,n){return n},sticky:"left"}})).concat(null===t||void 0===t?void 0:t.map((function(e){return{Header:String(e),accessor:String(e)}})))}),[t,b]);return(0,o.useMemo)((function(){return null===v||void 0===v?void 0:v.map((function(e){return e.reduce((function(e,n,i){return S(S({},e),{},(0,r.Z)({},t[i],n))}),{})}))}),[t,v]),(0,k.jsx)(C,{columnHeaderHeight:n,disableScrolling:i,height:u,maxHeight:(a||0)+37,noBorderBottom:d,noBorderLeft:s,noBorderRight:p,noBorderTop:f,children:(0,k.jsx)(N,{columnHeaderHeight:n,columns:y,data:v,disableScrolling:i,height:u,index:l,invalidValues:c,maxHeight:a,numberOfIndexes:b,previewIndexes:h,renderColumnHeader:m,width:g})})}},27125:function(e,n,t){"use strict";var r=t(82684),i=t(12691),o=t.n(i),u=t(34376),l=t.n(u),c=t(9518),a=t(66050),d=t(60328),s=t(16634),p=t(10919),f=t(98781),h=t(86673),m=t(17903),v=t(19711),g=t(10503),b=t(49125),y=t(44162),x=t(24224),O=t(28598);n.Z=function(e){var n=e.blockRuns,t=e.onClickRow,i=e.pipeline,u=e.selectedRun,j=(0,r.useContext)(c.ThemeContext),w=(i||{}).uuid,Z=(0,r.useMemo)((function(){return i.blocks||[]}),[i]),P=(0,r.useMemo)((function(){return(0,x.HK)(Z,(function(e){return e.uuid}))}),[Z]);return(0,O.jsx)(m.Z,{columnFlex:[null,1,3,2,null,null],columns:[{uuid:"Date"},{uuid:"Status"},{uuid:"Trigger"},{uuid:"Block"},{uuid:"Completed"},{uuid:"Logs"}],isSelectedRow:function(e){return n[e].id===(null===u||void 0===u?void 0:u.id)},onClickRow:t,rows:null===n||void 0===n?void 0:n.map((function(e){var n,t,r,u=e.block_uuid,c=e.completed_at,m=e.created_at,x=e.id,Z=e.pipeline_schedule_id,E=e.pipeline_schedule_name,k=e.status,_=u,S=_.split(":");f.q.INTEGRATION===i.type&&(_=S[0],t=S[1],r=S[2]);var D=P[_];return D||(D=P[S[0]]),[(0,O.jsx)(v.ZP,{monospace:!0,default:!0,children:m}),(0,O.jsx)(v.ZP,{danger:a.V.FAILED===k,default:a.V.CANCELLED===k,info:a.V.INITIAL===k,monospace:!0,success:a.V.COMPLETED===k,warning:a.V.RUNNING===k,children:k}),(0,O.jsx)(o(),{as:"/pipelines/".concat(w,"/triggers/").concat(Z),href:"/pipelines/[pipeline]/triggers/[...slug]",passHref:!0,children:(0,O.jsx)(p.Z,{bold:!0,sameColorAsText:!0,children:E})}),(0,O.jsx)(o(),{as:"/pipelines/".concat(w,"/edit?block_uuid=").concat(_),href:"/pipelines/[pipeline]/edit",passHref:!0,children:(0,O.jsxs)(p.Z,{bold:!0,sameColorAsText:!0,verticalAlignContent:!0,children:[(0,O.jsx)(s.Z,{color:(0,y.qn)(null===(n=D)||void 0===n?void 0:n.type,{theme:j}).accent,size:1.5*b.iI,square:!0}),(0,O.jsx)(h.Z,{mr:1}),(0,O.jsxs)(v.ZP,{monospace:!0,children:[_,t&&": ",t&&(0,O.jsx)(v.ZP,{default:!0,inline:!0,monospace:!0,children:t}),r>=0&&": ",r>=0&&(0,O.jsx)(v.ZP,{default:!0,inline:!0,monospace:!0,children:r})]})]})}),(0,O.jsx)(v.ZP,{monospace:!0,default:!0,children:c||"-"}),(0,O.jsx)(d.Z,{default:!0,iconOnly:!0,noBackground:!0,onClick:function(){return l().push("/pipelines/".concat(w,"/logs?block_run_id[]=").concat(x))},children:(0,O.jsx)(g.B4,{default:!0,size:2*b.iI})})]})),uuid:"block-runs"})}},64155:function(e,n,t){"use strict";t.d(n,{Eh:function(){return c},ht:function(){return d},t0:function(){return a}});var r=t(9518),i=t(82386),o=t(32151),u=t(31012),l=t(49125),c=(l.iI,o.O$+3*l.iI+u.dN),a=r.default.div.withConfig({displayName:"indexstyle__SidekickContainerStyle",componentId:"sc-15ofupc-0"})(["position:relative;width:fit-content;"," ",""],(function(e){return"\n    height: calc(100vh - ".concat(i.uX,"px - ").concat(e.heightOffset,"px);\n  ")}),(function(e){return e.fullWidth&&"\n    width: 100%;\n  "})),d=r.default.div.withConfig({displayName:"indexstyle__PaddingContainerStyle",componentId:"sc-15ofupc-1"})(["padding:","px;",""],2*l.iI,(function(e){return e.noPadding&&"\n    padding: 0;\n  "}))},19395:function(e,n,t){"use strict";t.d(n,{IJ:function(){return d},eI:function(){return s},gU:function(){return f},tL:function(){return p},vJ:function(){return h}});var r,i,o=t(82394),u=t(92083),l=t.n(u);function c(e,n){var t=Object.keys(e);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(e);n&&(r=r.filter((function(n){return Object.getOwnPropertyDescriptor(e,n).enumerable}))),t.push.apply(t,r)}return t}function a(e){for(var n=1;n<arguments.length;n++){var t=null!=arguments[n]?arguments[n]:{};n%2?c(Object(t),!0).forEach((function(n){(0,o.Z)(e,n,t[n])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(t)):c(Object(t)).forEach((function(n){Object.defineProperty(e,n,Object.getOwnPropertyDescriptor(t,n))}))}return e}function d(e){return null===e||void 0===e?void 0:e.reduce((function(e,n){var t=n.block_uuid,r=n.completed_at,i=n.started_at,u=n.status,c=null;i&&r&&(c=l()(r).valueOf()-l()(i).valueOf());return a(a({},e),{},(0,o.Z)({},t,{runtime:c,status:u}))}),{})}function s(e){if(!e)return null;var n=new Date(l()(e).valueOf()),t=Date.UTC(n.getFullYear(),n.getMonth(),n.getDate(),n.getHours(),n.getMinutes(),n.getSeconds());return new Date(t)}!function(e){e.DAY="day",e.HOUR="hour",e.MINUTE="minute",e.SECOND="second"}(i||(i={}));var p=(r={},(0,o.Z)(r,i.DAY,86400),(0,o.Z)(r,i.HOUR,3600),(0,o.Z)(r,i.MINUTE,60),(0,o.Z)(r,i.SECOND,1),r);function f(e){var n=i.SECOND,t=e;return e%86400===0?(t/=86400,n=i.DAY):e%3600===0?(t/=3600,n=i.HOUR):e%60===0&&(t/=60,n=i.MINUTE),{time:t,unit:n}}function h(e,n){return e*p[n]}},82635:function(e,n,t){"use strict";var r,i;t.d(n,{Gi:function(){return i},jU:function(){return u},uF:function(){return r}}),function(e){e.BUSY="busy",e.IDLE="idle",e.QUEUED="queued"}(r||(r={})),function(e){e.IMAGE_PNG="image/png",e.PROGRESS="progress",e.TABLE="table",e.TEXT="text",e.TEXT_HTML="text/html",e.TEXT_PLAIN="text/plain"}(i||(i={}));var o,u=[i.TEXT,i.TEXT_PLAIN];!function(e){e.DISPLAY_DATA="display_data",e.STATUS="status",e.STREAM="stream",e.STREAM_PIPELINE="stream_pipeline"}(o||(o={}))},47409:function(e,n,t){"use strict";t.d(n,{D:function(){return u},V:function(){return o}});var r,i=t(82394),o=t(66050).V,u=(r={},(0,i.Z)(r,o.CANCELLED,"Cancelled"),(0,i.Z)(r,o.COMPLETED,"Done"),(0,i.Z)(r,o.FAILED,"Failed"),(0,i.Z)(r,o.INITIAL,"Ready"),(0,i.Z)(r,o.RUNNING,"Running"),r)},23588:function(e,n,t){"use strict";t.r(n),t.d(n,{default:function(){return B}});var r=t(77837),i=t(12757),o=t(82394),u=t(38860),l=t.n(u),c=t(82684),a=t(83455),d=t(27125),s=t(60328),p=t(34744),f=t(87372),h=t(38965),m=t(47409),v=t(86673),g=t(41374),b=t(26304),y=t(62976),x=t(86532),O=t(67971),j=t(54283),w=t(19711),Z=t(82635),P=t(64155),E=t(19395),k=t(5679),_=t(28598),S=["blockRuns","columns","dataType","height","heightOffset","loadingData","pipeline","renderColumnHeader","rows","selectedRun","textData"];function D(e,n){var t=Object.keys(e);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(e);n&&(r=r.filter((function(n){return Object.getOwnPropertyDescriptor(e,n).enumerable}))),t.push.apply(t,r)}return t}function I(e){for(var n=1;n<arguments.length;n++){var t=null!=arguments[n]?arguments[n]:{};n%2?D(Object(t),!0).forEach((function(n){(0,o.Z)(e,n,t[n])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(t)):D(Object(t)).forEach((function(n){Object.defineProperty(e,n,Object.getOwnPropertyDescriptor(t,n))}))}return e}var C=t(59920),T=t(49125),N=t(96510),R=t(66653);function H(e,n){var t=Object.keys(e);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(e);n&&(r=r.filter((function(n){return Object.getOwnPropertyDescriptor(e,n).enumerable}))),t.push.apply(t,r)}return t}function M(e){for(var n=1;n<arguments.length;n++){var t=null!=arguments[n]?arguments[n]:{};n%2?H(Object(t),!0).forEach((function(n){(0,o.Z)(e,n,t[n])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(t)):H(Object(t)).forEach((function(n){Object.defineProperty(e,n,Object.getOwnPropertyDescriptor(t,n))}))}return e}function A(e){var n,t=e.pipeline,r=e.pipelineRun,o=(0,c.useState)(),u=o[0],l=o[1],D=t.uuid,H=g.ZP.pipelines.detail(D).data,A=(0,c.useMemo)((function(){return M(M({},null===H||void 0===H?void 0:H.pipeline),{},{uuid:D})}),[H,D]),B=g.ZP.pipeline_runs.detail(r.id,{},{refreshInterval:3e3,revalidateOnFocus:!0}).data,L=(0,c.useMemo)((function(){return null===B||void 0===B?void 0:B.pipeline_run}),[B]),U=(0,a.Db)(g.ZP.pipeline_runs.useUpdate(null===L||void 0===L?void 0:L.id),{onSuccess:function(e){return(0,N.wD)(e,{onErrorCallback:function(e){var n=e.error,t=n.errors,r=n.message;console.log(t,r)}})}}),V=(0,i.Z)(U,2),F=V[0],G=V[1].isLoading,X=g.ZP.outputs.block_runs.list(null===u||void 0===u?void 0:u.id),W=X.data,q=X.loading;X.mutate;console.log("dataOutput:",W);var J=(null===W||void 0===W||null===(n=W.outputs)||void 0===n?void 0:n[0])||{},Y=J.sample_data,z=J.text_data,K=J.type,Q=(0,c.useMemo)((function(){return null===L||void 0===L?void 0:L.block_runs}),[L]),$=((null===Y||void 0===Y?void 0:Y.columns)||[]).slice(0,40),ee=(null===Y||void 0===Y?void 0:Y.rows)||[],ne=(0,c.useMemo)((function(){return(0,_.jsx)(d.Z,{blockRuns:Q,onClickRow:function(e){return l((function(n){var t=Q[e];return(null===n||void 0===n?void 0:n.id)!==t.id?t:null}))},pipeline:A,selectedRun:u})}),[Q,A,u]);return(0,_.jsxs)(h.Z,{breadcrumbs:[{label:function(){return"Runs"},linkProps:{as:"/pipelines/".concat(D,"/runs"),href:"/pipelines/[pipeline]/runs"}},{label:function(){return null===L||void 0===L?void 0:L.execution_date}}],buildSidekick:function(e){return function(e){var n=e.blockRuns,t=e.columns,r=e.dataType,i=e.height,o=e.heightOffset,u=e.loadingData,l=e.pipeline,c=e.renderColumnHeader,a=e.rows,d=e.selectedRun,s=e.textData,p=I({},(0,b.Z)(e,S));p.blockStatus=(0,E.IJ)(n);var h=(0,_.jsx)(v.Z,{ml:2,children:(0,_.jsx)(w.ZP,{children:"This block run has no output."})}),m=a&&a.length>0?(0,_.jsx)(y.Z,{columnHeaderHeight:c?P.Eh:0,columns:t,height:i-o-90,noBorderBottom:!0,noBorderLeft:!0,noBorderRight:!0,renderColumnHeader:c,rows:a}):h,g=(0,k.Pb)(s)?JSON.stringify(JSON.parse(s),null,2):s,D=s?(0,_.jsx)(v.Z,{ml:2,children:(0,_.jsx)(w.ZP,{monospace:!0,children:(0,_.jsx)("pre",{children:g})})}):h;return(0,_.jsxs)(_.Fragment,{children:[!d&&(0,_.jsx)(x.Z,I(I({},p),{},{height:i,heightOffset:o||0,pipeline:l})),d&&(0,_.jsxs)(_.Fragment,{children:[(0,_.jsx)(v.Z,{pl:2,py:3,style:{position:"fixed"},children:(0,_.jsx)(f.Z,{level:4,muted:!0,children:"Block Output"})}),(0,_.jsxs)("div",{style:{position:"relative",top:"75px"},children:[u&&(0,_.jsx)(v.Z,{mt:2,children:(0,_.jsx)(O.Z,{alignItems:"center",fullWidth:!0,justifyContent:"center",children:(0,_.jsx)(j.Z,{color:"white",large:!0})})}),!u&&r===Z.Gi.TABLE&&m,!u&&r!==Z.Gi.TABLE&&D]})]})]})}(M(M({},e),{},{blockRuns:Q,columns:$,dataType:K,loadingData:q,rows:ee,selectedRun:u,textData:z}))},pageName:C.M.RUNS,pipeline:A,subheader:(null===L||void 0===L?void 0:L.status)&&L.status!==m.V.COMPLETED&&(0,_.jsx)(s.Z,{danger:!0,loading:G,onClick:function(e){(0,R.j)(e),F({pipeline_run:{action:"retry_blocks"}})},outline:!0,children:"Retry incomplete blocks"}),title:function(e){var n=e.name;return"".concat(n," runs")},uuid:"".concat(C.M.RUNS,"_").concat(D,"_").concat(null===L||void 0===L?void 0:L.id),children:[(0,_.jsx)(v.Z,{mt:T.cd,px:T.cd,children:(0,_.jsx)(f.Z,{level:5,children:"Block runs"})}),(0,_.jsx)(p.Z,{light:!0,mt:T.cd,short:!0}),ne]})}A.getInitialProps=function(){var e=(0,r.Z)(l().mark((function e(n){var t,r,i;return l().wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return t=n.query,r=t.pipeline,i=t.run,e.abrupt("return",{pipeline:{uuid:r},pipelineRun:{id:i}});case 2:case"end":return e.stop()}}),e)})));return function(n){return e.apply(this,arguments)}}();var B=A},39525:function(e,n,t){(window.__NEXT_P=window.__NEXT_P||[]).push(["/pipelines/[pipeline]/runs/[run]",function(){return t(23588)}])}},function(e){e.O(0,[4259,2212,7689,6674,4804,5872,1774,2125,1374,5763,6792,1273,8965,2151,5703,9774,2888,179],(function(){return n=39525,e(e.s=n);var n}));var n=e.O();_N_E=n}]);