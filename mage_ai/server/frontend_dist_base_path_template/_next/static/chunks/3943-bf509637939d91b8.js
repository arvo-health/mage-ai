"use strict";(self.webpackChunk_N_E=self.webpackChunk_N_E||[]).push([[3943],{4611:function(e,n,t){t.d(n,{f:function(){return o}});var i=t(38626),r=t(44897),u=t(70515),l=t(42631),o=i.default.div.withConfig({displayName:"Tablestyle__PopupContainerStyle",componentId:"sc-8ammqd-0"})(["position:absolute;max-height:","px;z-index:10;border-radius:","px;padding:","px;"," "," "," ",""],58*u.iI,l.TR,2*u.iI,(function(e){return"\n    box-shadow: ".concat((e.theme.shadow||r.Z.shadow).popup,";\n    background-color: ").concat((e.theme.interactive||r.Z.interactive).defaultBackground,";\n  ")}),(function(e){return e.leftOffset&&"\n    left: ".concat(e.leftOffset,"px;\n  ")}),(function(e){return e.topOffset&&"\n    top: ".concat(e.topOffset,"px;\n  ")}),(function(e){return e.width&&"\n    width: ".concat(e.width,"px;\n  ")}))},53943:function(e,n,t){var i=t(82394),r=t(75582),u=t(12691),l=t.n(u),o=t(83455),c=t(82684),s=t(34376),a=t(71180),d=t(70652),p=t(50724),f=t(97618),h=t(55485),v=t(48670),b=t(44265),g=t(89515),_=t(38276),x=t(4190),j=t(75499),O=t(30160),C=t(35686),E=t(44897),m=t(42631),Z=t(72473),I=t(81655),y=t(72191),w=t(4611),P=t(30229),k=t(31608),N=t(70515),L=t(16488),D=t(86735),R=t(50178),T=t(72619),A=t(3314),S=t(69419),V=t(28598);function U(e,n){var t=Object.keys(e);if(Object.getOwnPropertySymbols){var i=Object.getOwnPropertySymbols(e);n&&(i=i.filter((function(n){return Object.getOwnPropertyDescriptor(e,n).enumerable}))),t.push.apply(t,i)}return t}function F(e){for(var n=1;n<arguments.length;n++){var t=null!=arguments[n]?arguments[n]:{};n%2?U(Object(t),!0).forEach((function(n){(0,i.Z)(e,n,t[n])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(t)):U(Object(t)).forEach((function(n){Object.defineProperty(e,n,Object.getOwnPropertyDescriptor(t,n))}))}return e}var M={monospace:!0,small:!0};function H(e){var n=e.cancelingRunId,t=e.disabled,i=e.isLoadingCancelPipeline,u=e.onCancel,l=e.onSuccess,s=e.pipelineRun,d=e.setCancelingRunId,f=e.setErrors,v=e.setShowConfirmationId,g=e.showConfirmationId,j=(0,R.Ct)(),I=s||{},k=I.id,N=I.pipeline_schedule_id,L=I.pipeline_schedule_token,D=I.pipeline_schedule_type,A=I.status,U=i&&k===n&&b.VO.RUNNING===A,F=(0,S.iV)(),M=(0,c.useMemo)((function(){return(null!==F&&void 0!==F&&F.page?+F.page:0)>0}),[null===F||void 0===F?void 0:F.page]),H=(0,o.Db)(P.Xm.API===D&&L?C.ZP.pipeline_runs.pipeline_schedules.useCreateWithParent(N,L):C.ZP.pipeline_runs.pipeline_schedules.useCreate(N),{onSuccess:function(e){return(0,T.wD)(e,{callback:function(){l()},onErrorCallback:function(e,n){return null===f||void 0===f?void 0:f({errors:n,response:e})}})}}),z=(0,r.Z)(H,1)[0],Y=(0,c.useCallback)((function(){v(null),z({pipeline_run:{backfill_id:null===s||void 0===s?void 0:s.backfill_id,event_variables:(null===s||void 0===s?void 0:s.event_variables)||{},execution_date:null===s||void 0===s?void 0:s.execution_date,pipeline_schedule_id:null===s||void 0===s?void 0:s.pipeline_schedule_id,pipeline_uuid:null===s||void 0===s?void 0:s.pipeline_uuid,variables:(null===s||void 0===s?void 0:s.variables)||{}}})}),[z,s,v]),B=(0,c.useCallback)((function(){v(null),d(k),u({id:k,status:b.VO.CANCELLED})}),[u,k,d,v]);return(0,V.jsxs)("div",{style:{position:"relative"},children:[(0,V.jsx)(a.Z,{backgroundColor:U&&E.Z.accent.yellow,beforeIcon:b.VO.INITIAL!==A&&!t&&(0,V.jsxs)(V.Fragment,{children:[b.VO.COMPLETED===A&&(0,V.jsx)(Z.Jr,{size:y.bL}),[b.VO.FAILED,b.VO.CANCELLED].includes(A)&&(0,V.jsx)(Z.Py,{inverted:b.VO.CANCELLED===A&&!j,size:y.bL}),[b.VO.RUNNING].includes(A)&&(0,V.jsx)(x.Z,{color:U?E.Z.status.negative:E.Z.monotone.white,small:!0})]}),borderRadius:m.D7,danger:b.VO.FAILED===A&&!j,default:b.VO.INITIAL===A,disabled:t||j,loading:!s,onClick:function(){return v(k)},padding:"6px",primary:b.VO.RUNNING===A&&!U&&!j,warning:b.VO.CANCELLED===A&&!j,children:t?"Ready":U?"Canceling":b.Do[A]}),(0,V.jsx)(p.Z,{onClickOutside:function(){return v(null)},open:g===k,children:(0,V.jsxs)(w.f,{children:[[b.VO.RUNNING,b.VO.INITIAL].includes(A)&&(0,V.jsxs)(V.Fragment,{children:[(0,V.jsx)(O.ZP,{bold:!0,color:"#9ECBFF",children:"Run is in progress"}),(0,V.jsx)(_.Z,{mb:1}),(0,V.jsxs)(O.ZP,{children:["This pipeline run is currently ongoing. Retrying will cancel",(0,V.jsx)("br",{}),"the current pipeline run."]}),(0,V.jsx)(O.ZP,{}),(0,V.jsx)(_.Z,{mt:1,children:(0,V.jsxs)(h.ZP,{children:[(0,V.jsx)(a.Z,{onClick:function(){B(),Y()},children:"Retry run"}),(0,V.jsx)(_.Z,{ml:1}),(0,V.jsx)(a.Z,{onClick:B,children:"Cancel run"})]})})]}),[b.VO.CANCELLED,b.VO.FAILED,b.VO.COMPLETED].includes(A)&&(0,V.jsxs)(V.Fragment,{children:[(0,V.jsxs)(O.ZP,{bold:!0,color:"#9ECBFF",children:["Run ",A]}),(0,V.jsx)(_.Z,{mb:1}),(0,V.jsxs)(O.ZP,{children:["Retry the run with changes you have made to the pipeline.",M?(0,V.jsxs)(V.Fragment,{children:[(0,V.jsx)("br",{}),"Note that the retried run may appear on a previous page."]}):null]}),(0,V.jsx)(_.Z,{mb:1}),(0,V.jsx)(a.Z,{onClick:Y,children:"Retry run"})]})]})})]})}n.Z=function(e){var n=e.allowBulkSelect,t=e.allowDelete,u=e.deletePipelineRun,x=e.disableRowSelect,E=e.emptyMessage,w=void 0===E?"No runs available":E,P=e.fetchPipelineRuns,S=e.hideTriggerColumn,U=e.onClickRow,z=e.pipelineRuns,Y=e.selectedRun,B=e.selectedRuns,G=e.setSelectedRuns,J=e.setErrors,K=(0,s.useRouter)(),X=(0,R.Ct)(),q=(0,c.useRef)({}),Q=(0,c.useState)(null),W=Q[0],$=Q[1],ee=(0,c.useState)(null),ne=ee[0],te=ee[1],ie=(0,c.useState)(null),re=ie[0],ue=ie[1],le=(0,c.useState)(0),oe=le[0],ce=le[1],se=(0,c.useState)(0),ae=se[0],de=se[1],pe=(0,o.Db)((function(e){var n=e.id,t=e.status;return C.ZP.pipeline_runs.useUpdate(n)({pipeline_run:{status:t}})}),{onSuccess:function(e){return(0,T.wD)(e,{callback:function(){$(null),null===P||void 0===P||P()},onErrorCallback:function(e,n){$(null),null===J||void 0===J||J({errors:n,response:e})}})}}),fe=(0,r.Z)(pe,2),he=fe[0],ve=fe[1].isLoading,be=[null,1],ge=[{uuid:"Status"},{uuid:"Pipeline"}];S||(be.push(1),ge.push({uuid:"Trigger"})),be.push.apply(be,[1,1,null,null]),ge.push.apply(ge,[{uuid:"Execution date"},{uuid:"Completed at"},{uuid:"Block runs"},{uuid:"Logs"}]),t&&!X&&(be.push.apply(be,[null]),ge.push({label:function(){return""},uuid:"Delete"}));var _e=(0,c.useMemo)((function(){return z.every((function(e){var n=e.id;return!(null===B||void 0===B||!B[n])}))}),[z,B]);return n&&(be.unshift(null),ge.unshift({label:function(){return(0,V.jsx)(d.Z,{checked:_e,onClick:function(){var e=(0,D.HK)(z||[],(function(e){return e.id}));G(_e?{}:e)}})},uuid:"Selected"})),!x&&U&&(be.push(null),ge.push({label:function(){return""},uuid:"action"})),(0,V.jsx)(k.cl,{minHeight:30*N.iI,overflowVisible:!!ne,children:0===(null===z||void 0===z?void 0:z.length)?(0,V.jsx)(_.Z,{px:3,py:1,children:(0,V.jsx)(O.ZP,{bold:!0,default:!0,monospace:!0,muted:!0,children:w})}):(0,V.jsx)(j.Z,{columnFlex:be,columns:ge,isSelectedRow:function(e){return!x&&z[e].id===(null===Y||void 0===Y?void 0:Y.id)},onClickRow:x?null:U,rowVerticalPadding:6,rows:null===z||void 0===z?void 0:z.map((function(e,r){var o=e.block_runs_count,s=e.completed_block_runs_count,j=e.completed_at,C=e.execution_date,E=e.id,w=e.pipeline_schedule_id,k=e.pipeline_schedule_name,N=e.pipeline_uuid,D=e.status;q.current[E]=(0,c.createRef)();var R,T,Y=!E&&!D,Q="".concat(s," out of ").concat(o," block runs completed"),ee=[];r>0&&z[r-1].execution_date===e.execution_date&&z[r-1].pipeline_schedule_id===e.pipeline_schedule_id?(ee=[(0,V.jsx)(_.Z,{ml:1,children:(0,V.jsxs)(h.ZP,{alignItems:"center",children:[(0,V.jsx)(Z.TT,{size:y.bL,useStroke:!0}),(0,V.jsx)(a.Z,{borderRadius:m.D7,notClickable:!0,padding:"6px",children:(0,V.jsx)(O.ZP,{muted:!0,children:b.Do[D]})})]})},"row_status"),(0,V.jsx)(O.ZP,{default:!0,monospace:!0,muted:!0,children:N},"row_pipeline_uuid")],S||ee.push((0,V.jsx)(O.ZP,{default:!0,monospace:!0,muted:!0,children:"-"},"row_trigger_retry")),(R=ee).push.apply(R,[(0,V.jsx)(O.ZP,{default:!0,monospace:!0,muted:!0,children:"-"},"row_date_retry"),(0,c.createElement)(O.ZP,F(F({},M),{},{key:"row_completed",muted:!0}),j&&(0,L.Vx)(j)||"-"),(0,V.jsx)(l(),{as:"/pipelines/".concat(N,"/runs/").concat(E),href:"/pipelines/[pipeline]/runs/[run]",passHref:!0,children:(0,V.jsx)(v.Z,{bold:!0,muted:!0,title:Q,children:"".concat(s," / ").concat(o)})},"row_block_runs"),(0,V.jsx)(a.Z,{default:!0,iconOnly:!0,noBackground:!0,onClick:function(){return K.push("/pipelines/".concat(N,"/logs?pipeline_run_id[]=").concat(E))},children:(0,V.jsx)(Z.UL,{default:!0,size:y.bL})},"row_logs")])):(ee=[(0,V.jsx)(H,{cancelingRunId:W,disabled:Y,isLoadingCancelPipeline:ve,onCancel:he,onSuccess:P,pipelineRun:e,setCancelingRunId:$,setErrors:J,setShowConfirmationId:te,showConfirmationId:ne},"row_retry_button"),(0,V.jsx)(O.ZP,{default:!0,monospace:!0,children:N},"row_pipeline_uuid")],S||ee.push((0,V.jsx)(l(),{as:"/pipelines/".concat(N,"/triggers/").concat(w),href:"/pipelines/[pipeline]/triggers/[...slug]",passHref:!0,children:(0,V.jsx)(v.Z,{bold:!0,sky:!0,children:k})},"row_trigger")),(T=ee).push.apply(T,[(0,c.createElement)(O.ZP,F(F({},M),{},{default:!0,key:"row_date"}),C&&(0,L.Vx)(C)||"-"),(0,c.createElement)(O.ZP,F(F({},M),{},{default:!0,key:"row_completed"}),j&&(0,L.Vx)(j)||"-"),(0,V.jsx)(l(),{as:"/pipelines/".concat(N,"/runs/").concat(E),href:"/pipelines/[pipeline]/runs/[run]",passHref:!0,children:(0,V.jsx)(v.Z,{bold:!0,disabled:Y,sky:!0,title:Q,children:Y?"":"".concat(s," / ").concat(o)})},"row_block_runs"),(0,V.jsx)(a.Z,{default:!0,disabled:Y,iconOnly:!0,noBackground:!0,onClick:function(){return K.push("/pipelines/".concat(N,"/logs?pipeline_run_id[]=").concat(E))},children:(0,V.jsx)(Z.UL,{default:!0,size:y.bL})},"row_logs")]));if(t&&!X&&ee.push((0,V.jsxs)(V.Fragment,{children:[(0,V.jsx)(a.Z,{default:!0,iconOnly:!0,noBackground:!0,onClick:function(e){var n,t,i,r;(0,A.j)(e),ue(E),ce((null===(n=q.current[E])||void 0===n||null===(t=n.current)||void 0===t?void 0:t.offsetTop)||0),de((null===(i=q.current[E])||void 0===i||null===(r=i.current)||void 0===r?void 0:r.offsetLeft)||0)},ref:q.current[E],title:"Delete",children:(0,V.jsx)(Z.rF,{default:!0,size:y.bL})}),(0,V.jsx)(p.Z,{onClickOutside:function(){return ue(null)},open:re===E,children:(0,V.jsx)(g.Z,{danger:!0,left:(ae||0)-I.nH,onCancel:function(){return ue(null)},onClick:function(){ue(null),u(E)},title:"Are you sure you want to delete this run (id ".concat(E,' for trigger "').concat(k,'")?'),top:(oe||0)-(r<=1?I.oz:I.OK),width:I.Xx})})]})),n){var ie=!(null===B||void 0===B||!B[E]);ee.unshift((0,V.jsx)(d.Z,{checked:ie,onClick:function(){G((function(n){return F(F({},n),{},(0,i.Z)({},E,ie?null:e))}))}},"selected-pipeline-run-".concat(E)))}return!x&&U&&ee.push((0,V.jsx)(f.Z,{flex:1,justifyContent:"flex-end",children:(0,V.jsx)(Z._Q,{default:!0,size:y.bL})})),ee})),uuid:"pipeline-runs"})})}},16488:function(e,n,t){t.d(n,{IJ:function(){return d},M8:function(){return g},Vx:function(){return f},eI:function(){return p},gU:function(){return v},tL:function(){return h},vJ:function(){return b}});var i,r,u=t(82394),l=t(92083),o=t.n(l),c=t(4383);function s(e,n){var t=Object.keys(e);if(Object.getOwnPropertySymbols){var i=Object.getOwnPropertySymbols(e);n&&(i=i.filter((function(n){return Object.getOwnPropertyDescriptor(e,n).enumerable}))),t.push.apply(t,i)}return t}function a(e){for(var n=1;n<arguments.length;n++){var t=null!=arguments[n]?arguments[n]:{};n%2?s(Object(t),!0).forEach((function(n){(0,u.Z)(e,n,t[n])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(t)):s(Object(t)).forEach((function(n){Object.defineProperty(e,n,Object.getOwnPropertyDescriptor(t,n))}))}return e}function d(e){return null===e||void 0===e?void 0:e.reduce((function(e,n){var t=n.block_uuid,i=n.completed_at,r=n.started_at,l=n.status,c=null;r&&i&&(c=o()(i).valueOf()-o()(r).valueOf());return a(a({},e),{},(0,u.Z)({},t,{runtime:c,status:l}))}),{})}function p(e){if(!e)return null;var n=new Date(o()(e).valueOf()),t=Date.UTC(n.getFullYear(),n.getMonth(),n.getDate(),n.getHours(),n.getMinutes(),n.getSeconds());return new Date(t)}function f(e){return"string"!==typeof e?e:p(e.split("+")[0]).toISOString().split(".")[0]}!function(e){e.DAY="day",e.HOUR="hour",e.MINUTE="minute",e.SECOND="second"}(r||(r={}));var h=(i={},(0,u.Z)(i,r.DAY,86400),(0,u.Z)(i,r.HOUR,3600),(0,u.Z)(i,r.MINUTE,60),(0,u.Z)(i,r.SECOND,1),i);function v(e){var n=r.SECOND,t=e;return e%86400===0?(t/=86400,n=r.DAY):e%3600===0?(t/=3600,n=r.HOUR):e%60===0&&(t/=60,n=r.MINUTE),{time:t,unit:n}}function b(e,n){return e*h[n]}function g(e){var n,t="";return t="".concat(window.origin,"/api/pipeline_schedules/").concat(null===e||void 0===e?void 0:e.id,"/pipeline_runs"),null!==e&&void 0!==e&&e.token&&(t="".concat(t,"/").concat(e.token)),(n=window.location.port)&&(t=t.replace(n,c.QT)),t}},44265:function(e,n,t){t.d(n,{Az:function(){return c},BF:function(){return o},Do:function(){return a},IK:function(){return l},VO:function(){return u},sZ:function(){return s}});var i,r=t(82394),u=t(41143).V,l=[u.FAILED,u.COMPLETED,u.RUNNING,u.CANCELLED,u.INITIAL],o=[u.INITIAL,u.RUNNING],c=[u.CANCELLED,u.COMPLETED,u.FAILED],s="__mage_variables",a=(i={},(0,r.Z)(i,u.CANCELLED,"Cancelled"),(0,r.Z)(i,u.COMPLETED,"Done"),(0,r.Z)(i,u.FAILED,"Failed"),(0,r.Z)(i,u.INITIAL,"Ready"),(0,r.Z)(i,u.RUNNING,"Running"),i)},30229:function(e,n,t){t.d(n,{TR:function(){return d},U5:function(){return c},Xm:function(){return u},Z4:function(){return a},fq:function(){return o},kJ:function(){return s}});var i,r,u,l=t(82394);!function(e){e.API="api",e.EVENT="event",e.TIME="time"}(u||(u={}));var o,c,s,a=(i={},(0,l.Z)(i,u.API,(function(){return"API"})),(0,l.Z)(i,u.EVENT,(function(){return"event"})),(0,l.Z)(i,u.TIME,(function(){return"schedule"})),i);!function(e){e.ACTIVE="active",e.INACTIVE="inactive"}(o||(o={})),function(e){e.ONCE="@once",e.HOURLY="@hourly",e.DAILY="@daily",e.WEEKLY="@weekly",e.MONTHLY="@monthly"}(c||(c={})),function(e){e.CREATED_AT="created_at",e.NAME="name",e.PIPELINE="pipeline_uuid",e.STATUS="status",e.TYPE="schedule_type"}(s||(s={}));var d=(r={},(0,l.Z)(r,s.CREATED_AT,"Created at"),(0,l.Z)(r,s.NAME,"Name"),(0,l.Z)(r,s.PIPELINE,"Pipeline"),(0,l.Z)(r,s.STATUS,"Status"),(0,l.Z)(r,s.TYPE,"Type"),r)},72191:function(e,n,t){t.d(n,{bL:function(){return r},l2:function(){return u}});var i=t(70515),r=(i.iI,2*i.iI),u=(i.iI,3*i.iI)}}]);