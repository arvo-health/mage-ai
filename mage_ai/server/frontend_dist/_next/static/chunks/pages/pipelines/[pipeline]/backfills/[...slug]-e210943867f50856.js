(self.webpackChunk_N_E=self.webpackChunk_N_E||[]).push([[6780],{28358:function(e,n,t){"use strict";t.d(n,{Z:function(){return m}});var r=t(82684),i=t(60328),l=t(10919),c=t(86673),o=t(19711),a=t(10503),s=t(9518),u=t(23831),d=t(73942),p=t(49125),f=t(37391),h=s.default.div.withConfig({displayName:"indexstyle__ErrorPopupStyle",componentId:"sc-aqfw6f-0"})(["top:50%;left:50%;transform:translate(-50%,-50%);max-height:95vh;max-width:95vw;overflow:auto;padding:","px;position:fixed;z-index:100;border-radius:","px;"," ",""],p.iI*p.cd,d.n_,(function(e){return"\n    background-color: ".concat((e.theme||u.Z).background.page,";\n    border: 1px solid ").concat((e.theme||u.Z).accent.negative,";\n    box-shadow: ").concat((e.theme||u.Z).shadow.window,";\n  ")}),f.w5),b=s.default.div.withConfig({displayName:"indexstyle__CloseButtonContainerStyle",componentId:"sc-aqfw6f-1"})(["display:flex;justify-content:flex-end;position:sticky;top:0;"]),v=t(28598);var m=function(e){var n=e.displayMessage,t=e.errors,s=e.links,u=e.onClose,d=e.response,p=(0,r.useState)(!1),f=p[0],m=p[1],j=(0,r.useState)(!1),x=j[0],g=j[1],Z=(t||{}).messages,y=(null===d||void 0===d?void 0:d.error)||{},O=y.errors,k=y.exception;return(0,v.jsxs)(h,{children:[(0,v.jsx)(b,{children:(0,v.jsx)(i.Z,{iconOnly:!0,noBackground:!0,noBorder:!0,noPadding:!0,onClick:u,title:"Close errors",children:(0,v.jsx)(a.x8,{})})}),(0,v.jsx)(o.ZP,{bold:!0,large:!0,children:"Error"}),n&&(0,v.jsx)(c.Z,{mt:1,children:(0,v.jsx)(o.ZP,{default:!0,children:n})}),k&&(0,v.jsx)(c.Z,{mt:1,children:(0,v.jsx)(o.ZP,{default:!0,disableWordBreak:!0,monospace:!0,children:k})}),(null===Z||void 0===Z?void 0:Z.length)>0&&(0,v.jsxs)(c.Z,{mt:2,children:[(0,v.jsxs)(o.ZP,{bold:!0,large:!0,children:["Traceback (",(0,v.jsxs)(l.Z,{onClick:function(){return g((function(e){return!e}))},preventDefault:!0,warning:!0,children:[x?"hide":"show"," traceback"]}),")"]}),x&&(0,v.jsx)(c.Z,{mt:1,children:Z.map((function(e){return(0,v.jsx)(o.ZP,{dangerouslySetInnerHTML:{__html:e.replaceAll(" ","&nbsp;")},default:!0,disableWordBreak:!0,monospace:!0},e)}))})]}),O&&(0,v.jsxs)(c.Z,{mt:2,children:[(0,v.jsxs)(o.ZP,{bold:!0,large:!0,children:["Stack trace (",(0,v.jsxs)(l.Z,{onClick:function(){return m((function(e){return!e}))},preventDefault:!0,warning:!0,children:[f?"hide":"show"," stack trace"]}),")"]}),f&&(0,v.jsx)(c.Z,{mt:1,children:O.map((function(e){return(0,v.jsx)(o.ZP,{dangerouslySetInnerHTML:{__html:e.replaceAll(" ","&nbsp;")},default:!0,disableWordBreak:!0,monospace:!0},e)}))})]}),null===s||void 0===s?void 0:s.map((function(e,n){var t=e.label,r=e.onClick;return(0,v.jsx)(c.Z,{mt:2,children:(0,v.jsx)(l.Z,{large:!0,onClick:r,underline:!0,warning:!0,children:t})},t)}))]})}},2850:function(e,n,t){"use strict";t.d(n,{M:function(){return c}});var r=t(9518),i=t(23831),l=t(3055),c=r.default.div.withConfig({displayName:"indexstyle__BeforeStyle",componentId:"sc-12ee2ib-0"})(["min-height:calc(100vh - ","px);",""],l.Mz,(function(e){return"\n    border-left: 1px solid ".concat((e.theme.borders||i.Z.borders).medium,";\n  ")}))},56681:function(e,n,t){"use strict";t.d(n,{G:function(){return g},Z:function(){return Z}});var r=t(12757),i=t(82394),l=t(26304),c=t(32316),o=t(22673),a=t(86532),s=t(86673),u=t(19711),d=t(17903),p=t(49125),f=t(19395),h=t(28598),b=["height","heightOffset","pipeline","selectedRun","selectedTab","setSelectedTab"];function v(e,n){var t=Object.keys(e);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(e);n&&(r=r.filter((function(n){return Object.getOwnPropertyDescriptor(e,n).enumerable}))),t.push.apply(t,r)}return t}function m(e){for(var n=1;n<arguments.length;n++){var t=null!=arguments[n]?arguments[n]:{};n%2?v(Object(t),!0).forEach((function(n){(0,i.Z)(e,n,t[n])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(t)):v(Object(t)).forEach((function(n){Object.defineProperty(e,n,Object.getOwnPropertyDescriptor(t,n))}))}return e}var j={uuid:"Run details"},x={uuid:"Dependency tree"},g=[x,j];function Z(e){var n=e.height,t=e.heightOffset,i=e.pipeline,v=e.selectedRun,Z=e.selectedTab,y=e.setSelectedTab,O=m({},(0,l.Z)(e,b));v?O.blockStatus=(0,f.IJ)(null===v||void 0===v?void 0:v.block_runs):O.noStatus=!0;var k=(null===v||void 0===v?void 0:v.variables)||{};null!==v&&void 0!==v&&v.event_variables&&(k.event=v.event_variables);var P=[];k&&JSON.stringify(k,null,2).split("\n").forEach((function(e){P.push("    ".concat(e))}));var _=v&&[["Run ID",null===v||void 0===v?void 0:v.id],["Variables",(0,h.jsx)(o.Z,{language:"json",small:!0,source:P.join("\n")})]],w=v&&(0,h.jsx)(s.Z,{pb:p.cd,px:p.cd,children:(0,h.jsx)(d.Z,{alignTop:!0,columnFlex:[null,1],columnMaxWidth:function(e){return 1===e?"100px":null},rows:_.map((function(e){var n=(0,r.Z)(e,2),t=n[0],i=n[1];return[(0,h.jsx)(u.ZP,{monospace:!0,muted:!0,children:t}),(0,h.jsx)(u.ZP,{monospace:!0,textOverflow:!0,children:i})]})),uuid:"LogDetail"})}),I=Z&&y;return(0,h.jsxs)(h.Fragment,{children:[I&&(0,h.jsx)(s.Z,{py:p.cd,children:(0,h.jsx)(c.Z,{onClickTab:y,selectedTabUUID:null===Z||void 0===Z?void 0:Z.uuid,tabs:g})}),(!I||x.uuid===(null===Z||void 0===Z?void 0:Z.uuid))&&(0,h.jsx)(a.Z,m(m({},O),{},{height:n,heightOffset:(t||0)+(I?76:0),pipeline:i})),j.uuid===(null===Z||void 0===Z?void 0:Z.uuid)&&w]})}},58122:function(e,n,t){"use strict";t.d(n,{CL:function(){return f},FS:function(){return h},JZ:function(){return v},e7:function(){return m},v0:function(){return p},wx:function(){return b}});var r=t(12757),i=t(82394),l=t(43313),c=t(93348),o=t(32151),a=t(90211),s=t(84779);function u(e,n){var t=Object.keys(e);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(e);n&&(r=r.filter((function(n){return Object.getOwnPropertyDescriptor(e,n).enumerable}))),t.push.apply(t,r)}return t}function d(e){for(var n=1;n<arguments.length;n++){var t=null!=arguments[n]?arguments[n]:{};n%2?u(Object(t),!0).forEach((function(n){(0,i.Z)(e,n,t[n])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(t)):u(Object(t)).forEach((function(n){Object.defineProperty(e,n,Object.getOwnPropertyDescriptor(t,n))}))}return e}function p(e){var n=e.statistics,t=Object.keys(n),r=Array(l.Dy.length).fill(0);return 0===t.length?null:(t.forEach((function(e){if(l.Dy.includes(e)){var t=l.CC[e],i=n[e],c=i,o=!1,a=[2,3],u=l.Ub[e],d=l.oH[e],p=l.OD[e];if(l.y_.includes(e))o=!0,a=[2,1,2];else if(e in l.Sq){i=(0,s.Jw)(i,0);var f=l.Sq[e];c=n[f]}var h={columnFlexNumbers:a,name:t,progress:o,rate:c,successDirection:d,warning:p};l.y_.includes(e)||(h.value=i),r[u]=h}})),r)}function f(e){var n=e.columnTypes,t=void 0===n?{}:n,r=e.statistics,i=Object.keys(r);if(0===i.length)return null;var c=Object.values(t),s=c.length,u=[];u.push({name:"Column count",successDirection:l.oH.column_count,value:(0,a.x6)(s)}),i.forEach((function(e){if(l.Zu.includes(e)){var n=l.CC[e],t=r[e],i=l.OD[e];u.push({name:n,successDirection:l.oH[e],value:(0,a.x6)(t),warning:i})}}));var d=(0,o.QO)(c),p=d.countCategory,f=d.countDatetime,h=d.countNumerical;return u.push({name:"Categorical Features",rate:p/s,value:(0,a.x6)(p)},{name:"Numerical Features",rate:h/s,value:(0,a.x6)(h)},{name:"Datetime Features",rate:f/s,value:(0,a.x6)(f)}),u}function h(e){return"string"===typeof e?e:JSON.stringify(e)}function b(e,n){var t,r;return null===e||void 0===e||null===(t=e.find((function(e){var t=e.block;return n(t)})))||void 0===t||null===(r=t.variables)||void 0===r?void 0:r.map((function(e){var n=e.value;return d(d({},e),{},{value:h(n)})}))}function v(e,n){return n===c.Xm.TIME?e.push({uuid:"execution_date",value:"<run datetime>"}):n===c.Xm.EVENT&&e.push({uuid:"event",value:"<trigger event>"}),e}function m(e){return e?Object.entries(e).reduce((function(e,n){var t=(0,r.Z)(n,2),l=t[0],c=t[1],o=c;try{o=JSON.parse(c)}catch(a){}return d(d({},e),{},(0,i.Z)({},l,o))}),{}):e}},18025:function(e,n,t){"use strict";t.d(n,{J:function(){return a},U:function(){return o}});var r=t(9518),i=t(23831),l=t(73942),c=t(49125),o=r.default.div.withConfig({displayName:"indexstyle__CardStyle",componentId:"sc-m7tlau-0"})(["border-radius:","px;border-style:solid;border-width:2px;height:","px;margin-right:","px;padding:","px;width:","px;"," ",""],l.TR,14*c.iI,c.cd*c.iI,c.cd*c.iI,40*c.iI,(function(e){return!e.selected&&"\n    border-color: ".concat((e.theme.borders||i.Z.borders).light,";\n  ")}),(function(e){return e.selected&&"\n    border-color: ".concat((e.theme.interactive||i.Z.interactive).linkPrimary,";\n  ")})),a=r.default.div.withConfig({displayName:"indexstyle__DateSelectionContainer",componentId:"sc-m7tlau-1"})(["border-radius:","px;padding:","px;"," "," ",""],l.n_,c.tr,(function(e){return"\n    background-color: ".concat((e.theme.interactive||i.Z.interactive).defaultBackground,";\n  ")}),(function(e){return e.absolute&&"\n    position: absolute;\n    z-index: 2;\n    right: 0;\n    top: ".concat(2.5*c.iI,"px;\n  ")}),(function(e){return e.topPosition&&"\n    top: -".concat(42*c.iI,"px;\n  ")}))},43526:function(e,n,t){"use strict";t.d(n,{IB:function(){return a},VV:function(){return l},_7:function(){return c},rn:function(){return o}});var r,i=t(66050),l="datetime",c="code",o=i.V;!function(e){e.SECOND="second",e.MINUTE="minute",e.HOUR="hour",e.DAY="day",e.WEEK="week",e.MONTH="month",e.YEAR="year",e.CUSTOM="custom"}(r||(r={}));var a=[r.SECOND,r.MINUTE,r.HOUR,r.DAY,r.WEEK,r.MONTH,r.YEAR,r.CUSTOM]},2713:function(e,n,t){"use strict";var r=t(82394),i=t(44495),l=t(67971),c=t(55378),o=t(86673),a=t(19711),s=t(18025),u=t(49125),d=t(24224),p=t(28598);function f(e,n){var t=Object.keys(e);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(e);n&&(r=r.filter((function(n){return Object.getOwnPropertyDescriptor(e,n).enumerable}))),t.push.apply(t,r)}return t}function h(e){for(var n=1;n<arguments.length;n++){var t=null!=arguments[n]?arguments[n]:{};n%2?f(Object(t),!0).forEach((function(n){(0,r.Z)(e,n,t[n])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(t)):f(Object(t)).forEach((function(n){Object.defineProperty(e,n,Object.getOwnPropertyDescriptor(t,n))}))}return e}n.Z=function(e){var n=e.selectedDate,t=e.selectedTime,r=e.setSelectedDate,f=e.setSelectedTime,b=e.topPosition;return(0,p.jsxs)(s.J,{absolute:!0,topPosition:b,children:[(0,p.jsx)(i.ZP,{onChange:r,value:n}),(0,p.jsx)(o.Z,{mb:2}),(0,p.jsxs)(l.Z,{alignItems:"center",children:[(0,p.jsx)(a.ZP,{default:!0,large:!0,children:"Time (UTC):"}),(0,p.jsx)(o.Z,{pr:2}),(0,p.jsx)(c.Z,{compact:!0,monospace:!0,onChange:function(e){e.preventDefault(),f((function(n){return h(h({},n),{},{hour:e.target.value})}))},paddingRight:5*u.iI,placeholder:"HH",value:null===t||void 0===t?void 0:t.hour,children:(0,d.m5)(24,0).map((function(e){return String(e).padStart(2,"0")})).map((function(e){return(0,p.jsx)("option",{value:e,children:e},"hour_".concat(e))}))}),(0,p.jsx)(o.Z,{px:1,children:(0,p.jsx)(a.ZP,{bold:!0,large:!0,children:":"})}),(0,p.jsx)(c.Z,{compact:!0,monospace:!0,onChange:function(e){e.preventDefault(),f((function(n){return h(h({},n),{},{minute:e.target.value})}))},paddingRight:5*u.iI,placeholder:"MM",value:null===t||void 0===t?void 0:t.minute,children:(0,d.m5)(60,0).map((function(e){return String(e).padStart(2,"0")})).map((function(e){return(0,p.jsx)("option",{value:e,children:e},"minute_".concat(e))}))})]})]})}},22673:function(e,n,t){"use strict";var r=t(82684),i=t(73199),l=t.n(i),c=t(71593),o=t(9518),a=t(65292),s=t(23831),u=t(2005),d=t(49125),p=t(28598);n.Z=function(e){var n=e.language,t=e.maxWidth,i=e.showLineNumbers,f=e.small,h=e.source,b=e.wrapLines,v=(0,r.useContext)(o.ThemeContext);return(0,p.jsx)(l(),{source:h,renderers:{code:function(e){var r=e.value;return(0,p.jsx)(c.Z,{customStyle:{backgroundColor:(v.background||s.Z.background).popup,border:"none",borderRadius:"none",boxShadow:"none",fontFamily:u.Vp,fontSize:f?12:14,marginBottom:0,marginTop:0,paddingBottom:2*d.iI,paddingTop:2*d.iI,maxWidth:t},lineNumberStyle:{color:(v.content||s.Z.content).muted},language:n,showLineNumbers:i,style:a._4,useInlineStyles:!0,wrapLines:b,children:r})}}})}},32316:function(e,n,t){"use strict";t.d(n,{Z:function(){return h}});var r=t(82684),i=t(60328),l=t(67971),c=t(882),o=t(86673),a=t(99994),s=t(9518),u=t(49125),d=t(37391),p=s.default.div.withConfig({displayName:"indexstyle__TabsContainerStyle",componentId:"sc-segf7l-0"})(["padding-left:","px;padding-right:","px;"," "," ",""],u.cd*u.iI,u.cd*u.iI,(function(e){return e.noPadding&&"\n    padding: 0;\n  "}),(function(e){return e.allowScroll&&"\n    overflow: auto;\n  "}),d.w5),f=t(28598);var h=function(e){var n=e.allowScroll,t=e.contained,s=e.noPadding,d=e.onClickTab,h=e.selectedTabUUID,b=e.tabs,v=(0,r.useMemo)((function(){var e=b.length,n=[];return b.forEach((function(t,r){var s=t.Icon,p=t.IconSelected,b=t.label,v=t.uuid,m=v===h,j=m&&p||s,x=b?b():v,g=(0,f.jsxs)(l.Z,{alignItems:"center",children:[j&&(0,f.jsxs)(f.Fragment,{children:[(0,f.jsx)(j,{default:!m,size:2*u.iI}),(0,f.jsx)(o.Z,{mr:1})]}),x]});r>=1&&e>=2&&n.push((0,f.jsx)("div",{style:{marginLeft:1.5*u.iI}},"spacing-".concat(v))),m?n.push((0,f.jsx)(c.Z,{backgroundGradient:a.yr,backgroundPanel:!0,borderLess:!0,borderWidth:2,onClick:function(){return d(t)},paddingUnitsHorizontal:2,paddingUnitsVertical:1.25,children:g},v)):n.push((0,f.jsx)("div",{style:{padding:4},children:(0,f.jsx)(i.Z,{borderLess:!0,default:!0,onClick:function(){return d(t)},outline:!0,children:g},"button-tab-".concat(v))}))})),n}),[d,h,b]),m=(0,f.jsx)(l.Z,{alignItems:"center",children:v});return t?m:(0,f.jsx)(p,{allowScroll:n,noPadding:s,children:m})}},82944:function(e,n,t){"use strict";var r=t(82394),i=t(91835),l=t(82684),c=t(9518),o=t(69898),a=t(28598);function s(e,n){var t=Object.keys(e);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(e);n&&(r=r.filter((function(n){return Object.getOwnPropertyDescriptor(e,n).enumerable}))),t.push.apply(t,r)}return t}function u(e){for(var n=1;n<arguments.length;n++){var t=null!=arguments[n]?arguments[n]:{};n%2?s(Object(t),!0).forEach((function(n){(0,r.Z)(e,n,t[n])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(t)):s(Object(t)).forEach((function(n){Object.defineProperty(e,n,Object.getOwnPropertyDescriptor(t,n))}))}return e}var d=c.default.input.withConfig({displayName:"TextInput__TextInputStyle",componentId:"sc-1ii4qtc-0"})(["",""],o.p),p=function(e,n){var t=(0,i.Z)({},e);return(0,a.jsx)(o.Z,u(u({},t),{},{input:(0,a.jsx)(d,u({},t)),ref:n}))};n.Z=l.forwardRef(p)},12625:function(e,n,t){"use strict";t.r(n),t.d(n,{default:function(){return ne}});var r=t(12757),i=t(77837),l=t(82394),c=t(38860),o=t.n(c),a=t(82684),s=t(83455),u=t(34376),d=t(43526),p=t(60328),f=t(34744),h=t(67971),b=t(87372),v=t(51099),m=t(76623),j=t(97496),x=t(47409),g=t(55378),Z=t(86673),y=t(17903),O=t(19711),k=t(55170),P=t(56681),_=t(10503),w=t(2850),I=t(49125),S=t(59920),D=t(90211),C=t(58122),E=t(33766),N=t(7715),T=t(96510),M=t(66653),L=t(59e3),A=t(28598);function F(e,n){var t=Object.keys(e);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(e);n&&(r=r.filter((function(n){return Object.getOwnPropertyDescriptor(e,n).enumerable}))),t.push.apply(t,r)}return t}function U(e){for(var n=1;n<arguments.length;n++){var t=null!=arguments[n]?arguments[n]:{};n%2?F(Object(t),!0).forEach((function(n){(0,l.Z)(e,n,t[n])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(t)):F(Object(t)).forEach((function(n){Object.defineProperty(e,n,Object.getOwnPropertyDescriptor(t,n))}))}return e}var B=function(e){var n=e.backfill,t=e.fetchBackfill,i=e.pipeline,l=e.variables,c=(0,u.useRouter)(),o=n||{},F=o.block_uuid,B=o.end_datetime,R=o.id,H=o.interval_type,V=o.interval_units,z=o.name,Y=o.start_datetime,W=o.status,J=o.variables,q=void 0===J?{}:J,G=i.uuid,K=(0,L.iV)(),X={_limit:40,_offset:40*(null!==K&&void 0!==K&&K.page?K.page:0)};null!==K&&void 0!==K&&K.status&&(X.status=K.status);var Q=k.ZP.pipeline_runs.list(U(U({},X),{},{backfill_id:R,order_by:["id DESC"]}),{refreshInterval:3e3,revalidateOnFocus:!0},{pauseFetch:!R}),$=Q.data,ee=Q.mutate,ne=(0,a.useMemo)((function(){return(null===$||void 0===$?void 0:$.pipeline_runs)||[]}),[$]),te=(0,a.useMemo)((function(){return(null===$||void 0===$?void 0:$.total_count)||[]}),[$]),re=(0,a.useState)(null),ie=re[0],le=re[1],ce=(0,a.useMemo)((function(){var e=null!==K&&void 0!==K&&K.page?K.page:0;return(0,A.jsxs)(A.Fragment,{children:[(0,A.jsx)(j.Z,{fetchPipelineRuns:ee,onClickRow:function(e){return le((function(n){var t=ne[e];return(null===n||void 0===n?void 0:n.id)!==t.id?t:null}))},pipelineRuns:ne,selectedRun:ie}),(0,A.jsx)(Z.Z,{p:2,children:(0,A.jsx)(v.Z,{page:Number(e),maxPages:9,onUpdate:function(e){var n=Number(e),t=U(U({},K),{},{page:n>=0?n:0});c.push("/pipelines/[pipeline]/triggers/[...slug]","/pipelines/".concat(G,"/triggers/").concat(R,"?").concat((0,L.uM)(t)))},totalPages:Math.ceil(te/40)})})]})}),[ee,i,ne,ie]),oe=(0,a.useState)(P.G[0]),ae=oe[0],se=oe[1],ue=(0,s.Db)(k.ZP.backfills.useUpdate(R),{onSuccess:function(e){return(0,T.wD)(e,{callback:function(){t(),ee()},onErrorCallback:function(e,n){return console.log(n,e)}})}}),de=(0,r.Z)(ue,2),pe=de[0],fe=de[1].isLoading,he=(0,a.useMemo)((function(){return!!W&&(d.rn.CANCELLED!==W&&d.rn.FAILED!==W)}),[W]),be=(0,a.useMemo)((function(){return W&&d.rn.CANCELLED!==W&&d.rn.FAILED!==W&&d.rn.INITIAL!==W&&d.rn.RUNNING!==W}),[W]),ve=(0,a.useMemo)((function(){var e={default:!0,size:1.5*I.iI},n=[[(0,A.jsxs)(h.Z,{alignItems:"center",children:[(0,A.jsx)(_.VW,U({},e)),(0,A.jsx)(Z.Z,{mr:1}),(0,A.jsx)(O.ZP,{default:!0,children:"Backfill type"})]},"backfill_type_label"),(0,A.jsx)(O.ZP,{monospace:!0,children:F?d._7:d.VV},"backfill_type")],[(0,A.jsxs)(h.Z,{alignItems:"center",children:[(0,A.jsx)(_.rs,U({},e)),(0,A.jsx)(Z.Z,{mr:1}),(0,A.jsx)(O.ZP,{default:!0,children:"Status"})]},"backfill_status_label"),(0,A.jsx)(O.ZP,{danger:d.rn.CANCELLED===W||d.rn.FAILED==W,default:d.rn.INITIAL===W,monospace:!0,muted:!W,success:d.rn.RUNNING===W||d.rn.COMPLETED===W,children:W||"inactive"},"backfill_status")]];return F||n.push.apply(n,[[(0,A.jsxs)(h.Z,{alignItems:"center",children:[(0,A.jsx)(_.aw,U({},e)),(0,A.jsx)(Z.Z,{mr:1}),(0,A.jsx)(O.ZP,{default:!0,children:"Start date and time"})]},"backfill_start_date_label"),(0,A.jsx)(O.ZP,{monospace:!0,children:Y},"backfill_start_date")],[(0,A.jsxs)(h.Z,{alignItems:"center",children:[(0,A.jsx)(_.aw,U({},e)),(0,A.jsx)(Z.Z,{mr:1}),(0,A.jsx)(O.ZP,{default:!0,children:"End date and time"})]},"backfill_end_date_label"),(0,A.jsx)(O.ZP,{monospace:!0,children:B},"backfill_end_date")],[(0,A.jsxs)(h.Z,{alignItems:"center",children:[(0,A.jsx)(_.Pf,U({},e)),(0,A.jsx)(Z.Z,{mr:1}),(0,A.jsx)(O.ZP,{default:!0,children:"Interval type"})]},"interval_type_label"),(0,A.jsx)(O.ZP,{monospace:!0,children:H&&(0,D.kC)(H)},"interval_type")],[(0,A.jsxs)(h.Z,{alignItems:"center",children:[(0,A.jsx)(_.Pf,U({},e)),(0,A.jsx)(Z.Z,{mr:1}),(0,A.jsx)(O.ZP,{default:!0,children:"Interval units"})]},"interval_units_label"),(0,A.jsx)(O.ZP,{monospace:!0,children:V},"interval_units")]]),(0,A.jsx)(y.Z,{columnFlex:[null,1],rows:n})}),[F,B,H,V,he,Y,W]),me=(0,a.useMemo)((function(){return q||{}}),[q]),je=(0,a.useMemo)((function(){var e,n=[];return(0,N.Qr)(me)?n=(0,C.wx)(l,(function(e){return"global"===e.uuid})):Object.entries(me).forEach((function(e){var t=(0,r.Z)(e,2),i=t[0],l=t[1];n.push({uuid:i,value:(0,C.FS)(l)})})),"undefined"!==typeof n&&null!==(e=n)&&void 0!==e&&e.length?(0,A.jsx)(y.Z,{columnFlex:[null,1],rows:n.map((function(e){var n=e.uuid,t=e.value;return[(0,A.jsx)(O.ZP,{default:!0,monospace:!0,small:!0,children:n},"settings_variable_label_".concat(n)),(0,A.jsx)(O.ZP,{monospace:!0,small:!0,children:t},"settings_variable_".concat(n))]}))}):null}),[me,l]);return(0,A.jsx)(A.Fragment,{children:(0,A.jsxs)(m.Z,{afterHidden:!ie,before:(0,A.jsxs)(w.M,{children:[(0,A.jsxs)(Z.Z,{mb:I.HN,pt:I.cd,px:I.cd,children:[(0,A.jsx)(Z.Z,{mb:I.cd,children:(0,A.jsx)(_.yg,{size:5*I.iI})}),(0,A.jsx)(b.Z,{children:z})]}),(0,A.jsx)(Z.Z,{px:I.cd,children:(0,A.jsx)(b.Z,{level:5,children:"Settings"})}),(0,A.jsx)(f.Z,{light:!0,mt:1,short:!0}),ve,je&&(0,A.jsxs)(Z.Z,{my:I.HN,children:[(0,A.jsx)(Z.Z,{px:I.cd,children:(0,A.jsx)(b.Z,{level:5,children:"Runtime variables"})}),(0,A.jsx)(f.Z,{light:!0,mt:1,short:!0}),je]})]}),beforeWidth:34*I.iI,breadcrumbs:[{label:function(){return"Backfills"},linkProps:{as:"/pipelines/".concat(G,"/backfills"),href:"/pipelines/[pipeline]/backfills"}},{label:function(){return z},linkProps:{as:"/pipelines/".concat(G,"/backfills/").concat(R),href:"/pipelines/[pipeline]/backfills/[...slug]"}}],buildSidekick:function(e){return(0,P.Z)(U(U({},e),{},{selectedRun:ie,selectedTab:ae,setSelectedTab:se}))},pageName:S.M.BACKFILLS,pipeline:i,subheader:(0,A.jsxs)(h.Z,{alignItems:"center",children:[!be&&(0,A.jsxs)(A.Fragment,{children:[(0,A.jsx)(p.Z,{beforeIcon:he?(0,A.jsx)(_.dz,{size:2*I.iI}):(0,A.jsx)(_.Py,{inverted:!(d.rn.CANCELLED===W||d.rn.FAILED===W),size:2*I.iI}),danger:he,loading:fe,onClick:function(e){(0,M.j)(e),pe({backfill:{id:R,status:he?d.rn.CANCELLED:d.rn.INITIAL}})},outline:!0,success:!he&&!(d.rn.CANCELLED===W||d.rn.FAILED===W),children:he?"Cancel backfill":d.rn.CANCELLED===W||d.rn.FAILED===W?"Retry backfill":"Start backfill"}),(0,A.jsx)(Z.Z,{mr:I.cd})]}),(0,A.jsx)(p.Z,{linkProps:{as:"/pipelines/".concat(G,"/backfills/").concat(R,"/edit"),href:"/pipelines/[pipeline]/backfills/[...slug]"},noHoverUnderline:!0,outline:!0,sameColorAsText:!0,children:"Edit backfill"}),(0,A.jsx)(Z.Z,{mr:I.cd}),(0,A.jsxs)(g.Z,{compact:!0,defaultColor:!0,onChange:function(e){e.preventDefault(),"all"===e.target.value?c.push("/pipelines/[pipeline]/backfills/[...slug]","/pipelines/".concat(G,"/backfills/").concat(R)):(0,E.u)({page:0,status:e.target.value})},paddingRight:4*I.iI,placeholder:"Select run status",value:(null===K||void 0===K?void 0:K.status)||"all",children:[(0,A.jsx)("option",{value:"all",children:"All statuses"},"all_statuses"),Object.values(x.V).map((function(e){return(0,A.jsx)("option",{value:e,children:x.D[e]},e)}))]})]}),title:function(){return z},uuid:"backfill/detail",children:[(0,A.jsx)(Z.Z,{mt:I.cd,px:I.cd,children:(0,A.jsx)(b.Z,{level:5,children:"Runs for this backfill"})}),(0,A.jsx)(f.Z,{light:!0,mt:I.cd,short:!0}),ce]})})},R=t(2713),H=t(47999),V=t(28358),z=t(93461),Y=t(82944),W=[{label:function(){return"Date and time window"},description:function(){return"Backfill between a date and time range."},uuid:d.VV},{label:function(){return"Custom code"},description:function(){return"Use the output of a block to generate backfills."},uuid:d._7}],J=t(18025),q=t(19395);function G(e,n){var t=Object.keys(e);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(e);n&&(r=r.filter((function(n){return Object.getOwnPropertyDescriptor(e,n).enumerable}))),t.push.apply(t,r)}return t}function K(e){for(var n=1;n<arguments.length;n++){var t=null!=arguments[n]?arguments[n]:{};n%2?G(Object(t),!0).forEach((function(n){(0,l.Z)(e,n,t[n])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(t)):G(Object(t)).forEach((function(n){Object.defineProperty(e,n,Object.getOwnPropertyDescriptor(t,n))}))}return e}var X=function(e){var n=e.backfill,t=e.fetchBackfill,i=e.pipeline,l=(e.variables,(0,u.useRouter)()),c=(0,a.useState)(),o=c[0],v=c[1],j=o||{},x=j.block_uuid,P=j.id,w=j.interval_type,E=j.interval_units,M=(j.end_datetime,j.start_datetime,j.name),L=i.uuid,F=(0,a.useState)(null),U=F[0],B=F[1],G=(0,a.useState)({}),X=G[0],Q=(G[1],(0,a.useState)(x?d._7:d.VV)),$=Q[0],ee=Q[1],ne=(0,a.useState)(!1),te=ne[0],re=ne[1],ie=(0,a.useState)(!1),le=ie[0],ce=ie[1],oe=(0,a.useState)(null),ae=oe[0],se=oe[1],ue=(0,a.useState)(null),de=ue[0],pe=ue[1],fe=(0,a.useState)({hour:"00",minute:"00"}),he=fe[0],be=fe[1],ve=(0,a.useState)({hour:"00",minute:"00"}),me=ve[0],je=ve[1];(0,a.useEffect)((function(){if(n){v(n);var e=n.start_datetime;if(e){var t=e.split(" ")[1];pe((0,q.eI)(e)),je({hour:t.substring(0,2),minute:t.substring(3,5)})}var r=n.end_datetime;if(r){var i=r.split(" ")[1];se((0,q.eI)(r)),be({hour:i.substring(0,2),minute:i.substring(3,5)})}}}),[n]);var xe=(0,a.useMemo)((function(){var e=[[(0,A.jsxs)(h.Z,{alignItems:"center",children:[(0,A.jsx)(_.KJ,{default:!0,size:1.5*I.iI}),(0,A.jsx)(Z.Z,{mr:1}),(0,A.jsx)(O.ZP,{default:!0,children:"Backfill name"})]},"model_name_detail"),(0,A.jsx)(Y.Z,{monospace:!0,onChange:function(e){e.preventDefault(),v((function(n){return K(K({},n),{},{name:e.target.value})}))},placeholder:"Name this backfill",value:M},"model_name_input_detail")]];return d.VV===$&&e.push.apply(e,[[(0,A.jsxs)(h.Z,{alignItems:"center",children:[(0,A.jsx)(_.aw,{default:!0,size:1.5*I.iI}),(0,A.jsx)(Z.Z,{mr:1}),(0,A.jsx)(O.ZP,{default:!0,children:"Start date and time"})]},"start_time"),(0,A.jsxs)("div",{style:{minHeight:"".concat(5.75*I.iI,"px")},children:[!te&&(0,A.jsx)(Y.Z,{monospace:!0,onClick:function(){return re((function(e){return!e}))},onFocus:function(){return re(!0)},placeholder:"YYYY-MM-DD HH:MM",value:de?"".concat(de.toISOString().split("T")[0]," ").concat(null===me||void 0===me?void 0:me.hour,":").concat(null===me||void 0===me?void 0:me.minute):""}),(0,A.jsx)("div",{style:{width:"400px"},children:(0,A.jsx)(H.Z,{disableEscape:!0,onClickOutside:function(){return re(!1)},open:te,style:{position:"relative"},children:(0,A.jsx)(R.Z,{selectedDate:de,selectedTime:me,setSelectedDate:pe,setSelectedTime:je,topPosition:!0})})})]},"start_time_input")],[(0,A.jsxs)(h.Z,{alignItems:"center",children:[(0,A.jsx)(_.aw,{default:!0,size:1.5*I.iI}),(0,A.jsx)(Z.Z,{mr:1}),(0,A.jsx)(O.ZP,{default:!0,children:"End date and time"})]},"end_time"),(0,A.jsxs)("div",{style:{minHeight:"".concat(5.75*I.iI,"px")},children:[!le&&(0,A.jsx)(Y.Z,{monospace:!0,onClick:function(){return ce((function(e){return!e}))},onFocus:function(){return ce(!0)},placeholder:"YYYY-MM-DD HH:MM",value:ae?"".concat(ae.toISOString().split("T")[0]," ").concat(null===he||void 0===he?void 0:he.hour,":").concat(null===he||void 0===he?void 0:he.minute):""}),(0,A.jsx)("div",{style:{width:"400px"},children:(0,A.jsx)(H.Z,{disableEscape:!0,onClickOutside:function(){return ce(!1)},open:le,style:{position:"relative"},children:(0,A.jsx)(R.Z,{selectedDate:ae,selectedTime:he,setSelectedDate:se,setSelectedTime:be,topPosition:!0})})})]},"end_time_input")],[(0,A.jsxs)(h.Z,{alignItems:"center",children:[(0,A.jsx)(_.Pf,{default:!0,size:1.5*I.iI}),(0,A.jsx)(Z.Z,{mr:1}),(0,A.jsx)(O.ZP,{default:!0,children:"Interval type"})]},"interval_type"),(0,A.jsxs)(g.Z,{monospace:!0,onChange:function(e){e.preventDefault(),v((function(n){return K(K({},n),{},{interval_type:e.target.value})}))},placeholder:"Time spacing between each backfill",value:w,children:[!w&&(0,A.jsx)("option",{value:""}),d.IB.map((function(e){return(0,A.jsx)("option",{value:e,children:(0,D.kC)(e)},e)}))]},"interval_type_input")],[(0,A.jsxs)(h.Z,{alignItems:"center",children:[(0,A.jsx)(_.Pf,{default:!0,size:1.5*I.iI}),(0,A.jsx)(Z.Z,{mr:1}),(0,A.jsx)(O.ZP,{default:!0,children:"Interval units"})]},"interval_units"),(0,A.jsx)(Y.Z,{disabled:!w,monospace:!0,onChange:function(e){e.preventDefault(),v((function(n){return K(K({},n),{},{interval_units:e.target.value})}))},placeholder:w?"Number of ".concat(w," between each backfill"):"Interval type is required",type:"number",value:E},"interval_unit_input")]]),(0,A.jsxs)(A.Fragment,{children:[(0,A.jsx)(Z.Z,{mb:2,px:I.cd,children:(0,A.jsx)(b.Z,{children:"Settings"})}),(0,A.jsx)(f.Z,{light:!0,short:!0}),(0,A.jsx)(y.Z,{columnFlex:[null,1],rows:e})]})}),[ae,de,w,E,M,$,te,le,he,me]),ge=(0,s.Db)(k.ZP.backfills.useUpdate(P),{onSuccess:function(e){return(0,T.wD)(e,{callback:function(){t(),l.push("/pipelines/[pipeline]/backfills/[...slug]","/pipelines/".concat(L,"/backfills/").concat(P))},onErrorCallback:function(e,n){return B({errors:n,response:e})}})}}),Ze=(0,r.Z)(ge,2),ye=Ze[0],Oe=Ze[1].isLoading,ke=(0,a.useCallback)((function(){var e=K(K({},(0,N.GL)(o,["name"])),{},{end_datetime:null,interval_type:null,interval_units:null,start_datetime:null,variables:(0,C.e7)(X)});return d._7===$||(e.interval_type=w,e.interval_units=E,e.end_datetime=ae&&null!==he&&void 0!==he&&he.hour&&null!==he&&void 0!==he&&he.minute?"".concat(ae.toISOString().split("T")[0]," ").concat(null===he||void 0===he?void 0:he.hour,":").concat(null===he||void 0===he?void 0:he.minute,":00"):null,e.start_datetime=de&&null!==me&&void 0!==me&&me.hour&&null!==me&&void 0!==me&&me.minute?"".concat(de.toISOString().split("T")[0]," ").concat(null===me||void 0===me?void 0:me.hour,":").concat(null===me||void 0===me?void 0:me.minute,":00"):null),ye({backfill:e})}),[ae,de,w,E,o,X,$,he,me]),Pe=(0,a.useMemo)((function(){return d._7===$?!x:!(ae&&de&&w&&E)}),[x,ae,de,w,E,$,he,me]);return(0,A.jsxs)(A.Fragment,{children:[(0,A.jsxs)(m.Z,{breadcrumbs:[{label:function(){return"Backfills"},linkProps:{as:"/pipelines/".concat(L,"/backfills"),href:"/pipelines/[pipeline]/backfills"}},{label:function(){return null===o||void 0===o?void 0:o.name},linkProps:{as:"/pipelines/".concat(L,"/backfills/").concat(P),href:"/pipelines/[pipeline]/backfills/[...slug]"}}],pageName:S.M.BACKFILLS,pipeline:i,subheader:(0,A.jsxs)(h.Z,{alignItems:"center",children:[(0,A.jsx)(p.Z,{disabled:Pe,loading:Oe,onClick:ke,outline:!0,primary:!0,children:"Save changes"}),(0,A.jsx)(Z.Z,{mr:1}),(0,A.jsx)(p.Z,{linkProps:{href:"/pipelines/[pipeline]/backfills/[...slug]",as:"/pipelines/".concat(L,"/backfills/").concat(P)},noHoverUnderline:!0,outline:!0,sameColorAsText:!0,children:"Cancel"})]}),title:function(){return"Edit ".concat(null===o||void 0===o?void 0:o.name)},uuid:"backfill/edit",children:[(0,A.jsxs)(Z.Z,{p:I.cd,children:[(0,A.jsxs)(Z.Z,{mb:2,children:[(0,A.jsx)(b.Z,{children:"Backfill type"}),(0,A.jsx)(O.ZP,{muted:!0,children:"How would you like this pipeline to be backfilled?"})]}),(0,A.jsx)(h.Z,{children:W.map((function(e){var n=e.label,t=e.description,r=e.uuid,i=$===r,l=$&&!i;return(0,A.jsx)(p.Z,{noBackground:!0,noBorder:!0,noPadding:!0,onClick:function(){ee(r)},children:(0,A.jsx)(J.U,{selected:i,children:(0,A.jsxs)(h.Z,{alignItems:"center",children:[(0,A.jsx)(z.Z,{children:(0,A.jsx)("input",{checked:i,type:"radio"})}),(0,A.jsx)(Z.Z,{mr:I.cd}),(0,A.jsxs)(z.Z,{alignItems:"flex-start",flexDirection:"column",children:[(0,A.jsx)(b.Z,{bold:!0,default:!i&&!l,level:5,muted:!i&&l,children:n()}),(0,A.jsx)(O.ZP,{default:!i&&!l,leftAligned:!0,muted:l,children:t()})]})]})})},r)}))})]}),(0,A.jsx)(Z.Z,{mt:5,children:xe})]}),U&&(0,A.jsx)(H.Z,{disableClickOutside:!0,isOpen:!0,onClickOutside:function(){return B(null)},children:(0,A.jsx)(V.Z,K(K({},U),{},{onClose:function(){return B(null)}}))})]})};function Q(e,n){var t=Object.keys(e);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(e);n&&(r=r.filter((function(n){return Object.getOwnPropertyDescriptor(e,n).enumerable}))),t.push.apply(t,r)}return t}function $(e){for(var n=1;n<arguments.length;n++){var t=null!=arguments[n]?arguments[n]:{};n%2?Q(Object(t),!0).forEach((function(n){(0,l.Z)(e,n,t[n])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(t)):Q(Object(t)).forEach((function(n){Object.defineProperty(e,n,Object.getOwnPropertyDescriptor(t,n))}))}return e}function ee(e){var n=e.backfillId,t=e.pipelineUUID,r=e.subpath,i=k.ZP.variables.pipelines.list(t).data,l=(0,a.useMemo)((function(){return null===i||void 0===i?void 0:i.variables}),[i]),c=k.ZP.pipelines.detail(t,{includes_content:!1,includes_outputs:!1},{revalidateOnFocus:!1}).data,o=(0,a.useMemo)((function(){return $($({},null===c||void 0===c?void 0:c.pipeline),{},{uuid:t})}),[c,t]),s=k.ZP.backfills.detail(n),u=s.data,d=s.mutate,p=(0,a.useMemo)((function(){return null===u||void 0===u?void 0:u.backfill}),[u]);return"edit"===r?(0,A.jsx)(X,{backfill:p,fetchBackfill:d,pipeline:o,variables:l}):(0,A.jsx)(B,{backfill:p,fetchBackfill:d,pipeline:o,variables:l})}ee.getInitialProps=function(){var e=(0,i.Z)(o().mark((function e(n){var t,i,l,c,a,s;return o().wrap((function(e){for(;;)switch(e.prev=e.next){case 0:if(t=n.query,i=t.pipeline,l=t.slug,!Array.isArray(l)){e.next=4;break}return c=(0,r.Z)(l,2),a=c[0],s=c[1],e.abrupt("return",{backfillId:a,pipelineUUID:i,subpath:s});case 4:return e.abrupt("return",{pipelineUUID:i});case 5:case"end":return e.stop()}}),e)})));return function(n){return e.apply(this,arguments)}}();var ne=ee},53664:function(e,n,t){(window.__NEXT_P=window.__NEXT_P||[]).push(["/pipelines/[pipeline]/backfills/[...slug]",function(){return t(12625)}])}},function(e){e.O(0,[4259,2212,7689,6674,806,5872,1774,2524,4495,5170,714,9767,3323,1770,6623,9898,2151,5703,4846,9774,2888,179],(function(){return n=53664,e(e.s=n);var n}));var n=e.O();_N_E=n}]);