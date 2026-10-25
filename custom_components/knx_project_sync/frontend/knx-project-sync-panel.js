var z=globalThis,D=z.ShadowRoot&&(z.ShadyCSS===void 0||z.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,F=Symbol(),ie=new WeakMap,E=class{constructor(t,e,s){if(this._$cssResult$=!0,s!==F)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o,e=this.t;if(D&&t===void 0){let s=e!==void 0&&e.length===1;s&&(t=ie.get(e)),t===void 0&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),s&&ie.set(e,t))}return t}toString(){return this.cssText}},ne=n=>new E(typeof n=="string"?n:n+"",void 0,F),K=(n,...t)=>{let e=n.length===1?n[0]:t.reduce((s,i,r)=>s+(a=>{if(a._$cssResult$===!0)return a.cssText;if(typeof a=="number")return a;throw Error("Value passed to 'css' function must be a 'css' function result: "+a+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+n[r+1],n[0]);return new E(e,n,F)},re=(n,t)=>{if(D)n.adoptedStyleSheets=t.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(let e of t){let s=document.createElement("style"),i=z.litNonce;i!==void 0&&s.setAttribute("nonce",i),s.textContent=e.cssText,n.appendChild(s)}},B=D?n=>n:n=>n instanceof CSSStyleSheet?(t=>{let e="";for(let s of t.cssRules)e+=s.cssText;return ne(e)})(n):n;var{is:Se,defineProperty:Ee,getOwnPropertyDescriptor:Ce,getOwnPropertyNames:Te,getOwnPropertySymbols:Re,getPrototypeOf:Me}=Object,O=globalThis,ae=O.trustedTypes,je=ae?ae.emptyScript:"",Ne=O.reactiveElementPolyfillSupport,C=(n,t)=>n,W={toAttribute(n,t){switch(t){case Boolean:n=n?je:null;break;case Object:case Array:n=n==null?n:JSON.stringify(n)}return n},fromAttribute(n,t){let e=n;switch(t){case Boolean:e=n!==null;break;case Number:e=n===null?null:Number(n);break;case Object:case Array:try{e=JSON.parse(n)}catch{e=null}}return e}},de=(n,t)=>!Se(n,t),oe={attribute:!0,type:String,converter:W,reflect:!1,useDefault:!1,hasChanged:de};Symbol.metadata??=Symbol("metadata"),O.litPropertyMetadata??=new WeakMap;var v=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=oe){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){let s=Symbol(),i=this.getPropertyDescriptor(t,s,e);i!==void 0&&Ee(this.prototype,t,i)}}static getPropertyDescriptor(t,e,s){let{get:i,set:r}=Ce(this.prototype,t)??{get(){return this[e]},set(a){this[e]=a}};return{get:i,set(a){let c=i?.call(this);r?.call(this,a),this.requestUpdate(t,c,s)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??oe}static _$Ei(){if(this.hasOwnProperty(C("elementProperties")))return;let t=Me(this);t.finalize(),t.l!==void 0&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(C("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(C("properties"))){let e=this.properties,s=[...Te(e),...Re(e)];for(let i of s)this.createProperty(i,e[i])}let t=this[Symbol.metadata];if(t!==null){let e=litPropertyMetadata.get(t);if(e!==void 0)for(let[s,i]of e)this.elementProperties.set(s,i)}this._$Eh=new Map;for(let[e,s]of this.elementProperties){let i=this._$Eu(e,s);i!==void 0&&this._$Eh.set(i,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){let e=[];if(Array.isArray(t)){let s=new Set(t.flat(1/0).reverse());for(let i of s)e.unshift(B(i))}else t!==void 0&&e.push(B(t));return e}static _$Eu(t,e){let s=e.attribute;return s===!1?void 0:typeof s=="string"?s:typeof t=="string"?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),this.renderRoot!==void 0&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){let t=new Map,e=this.constructor.elementProperties;for(let s of e.keys())this.hasOwnProperty(s)&&(t.set(s,this[s]),delete this[s]);t.size>0&&(this._$Ep=t)}createRenderRoot(){let t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return re(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,s){this._$AK(t,s)}_$ET(t,e){let s=this.constructor.elementProperties.get(t),i=this.constructor._$Eu(t,s);if(i!==void 0&&s.reflect===!0){let r=(s.converter?.toAttribute!==void 0?s.converter:W).toAttribute(e,s.type);this._$Em=t,r==null?this.removeAttribute(i):this.setAttribute(i,r),this._$Em=null}}_$AK(t,e){let s=this.constructor,i=s._$Eh.get(t);if(i!==void 0&&this._$Em!==i){let r=s.getPropertyOptions(i),a=typeof r.converter=="function"?{fromAttribute:r.converter}:r.converter?.fromAttribute!==void 0?r.converter:W;this._$Em=i;let c=a.fromAttribute(e,r.type);this[i]=c??this._$Ej?.get(i)??c,this._$Em=null}}requestUpdate(t,e,s,i=!1,r){if(t!==void 0){let a=this.constructor;if(i===!1&&(r=this[t]),s??=a.getPropertyOptions(t),!((s.hasChanged??de)(r,e)||s.useDefault&&s.reflect&&r===this._$Ej?.get(t)&&!this.hasAttribute(a._$Eu(t,s))))return;this.C(t,e,s)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(t,e,{useDefault:s,reflect:i,wrapped:r},a){s&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,a??e??this[t]),r!==!0||a!==void 0)||(this._$AL.has(t)||(this.hasUpdated||s||(e=void 0),this._$AL.set(t,e)),i===!0&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}let t=this.scheduleUpdate();return t!=null&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[i,r]of this._$Ep)this[i]=r;this._$Ep=void 0}let s=this.constructor.elementProperties;if(s.size>0)for(let[i,r]of s){let{wrapped:a}=r,c=this[i];a!==!0||this._$AL.has(i)||c===void 0||this.C(i,void 0,r,c)}}let t=!1,e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(s=>s.hostUpdate?.()),this.update(e)):this._$EM()}catch(s){throw t=!1,this._$EM(),s}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(t){}firstUpdated(t){}};v.elementStyles=[],v.shadowRootOptions={mode:"open"},v[C("elementProperties")]=new Map,v[C("finalized")]=new Map,Ne?.({ReactiveElement:v}),(O.reactiveElementVersions??=[]).push("2.1.2");var Z=globalThis,le=n=>n,H=Z.trustedTypes,pe=H?H.createPolicy("lit-html",{createHTML:n=>n}):void 0,fe="$lit$",b=`lit$${Math.random().toFixed(9).slice(2)}$`,_e="?"+b,Pe=`<${_e}>`,k=document,R=()=>k.createComment(""),M=n=>n===null||typeof n!="object"&&typeof n!="function",Q=Array.isArray,Le=n=>Q(n)||typeof n?.[Symbol.iterator]=="function",Y=`[ 	
\f\r]`,T=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,ce=/-->/g,he=/>/g,$=RegExp(`>|${Y}(?:([^\\s"'>=/]+)(${Y}*=${Y}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),ue=/'/g,ge=/"/g,ve=/^(?:script|style|textarea|title)$/i,ee=n=>(t,...e)=>({_$litType$:n,strings:t,values:e}),d=ee(1),qe=ee(2),Je=ee(3),w=Symbol.for("lit-noChange"),h=Symbol.for("lit-nothing"),me=new WeakMap,y=k.createTreeWalker(k,129);function be(n,t){if(!Q(n)||!n.hasOwnProperty("raw"))throw Error("invalid template strings array");return pe!==void 0?pe.createHTML(t):t}var ze=(n,t)=>{let e=n.length-1,s=[],i,r=t===2?"<svg>":t===3?"<math>":"",a=T;for(let c=0;c<e;c++){let o=n[c],p,l,u=-1,m=0;for(;m<o.length&&(a.lastIndex=m,l=a.exec(o),l!==null);)m=a.lastIndex,a===T?l[1]==="!--"?a=ce:l[1]!==void 0?a=he:l[2]!==void 0?(ve.test(l[2])&&(i=RegExp("</"+l[2],"g")),a=$):l[3]!==void 0&&(a=$):a===$?l[0]===">"?(a=i??T,u=-1):l[1]===void 0?u=-2:(u=a.lastIndex-l[2].length,p=l[1],a=l[3]===void 0?$:l[3]==='"'?ge:ue):a===ge||a===ue?a=$:a===ce||a===he?a=T:(a=$,i=void 0);let _=a===$&&n[c+1].startsWith("/>")?" ":"";r+=a===T?o+Pe:u>=0?(s.push(p),o.slice(0,u)+fe+o.slice(u)+b+_):o+b+(u===-2?c:_)}return[be(n,r+(n[e]||"<?>")+(t===2?"</svg>":t===3?"</math>":"")),s]},j=class n{constructor({strings:t,_$litType$:e},s){let i;this.parts=[];let r=0,a=0,c=t.length-1,o=this.parts,[p,l]=ze(t,e);if(this.el=n.createElement(p,s),y.currentNode=this.el.content,e===2||e===3){let u=this.el.content.firstChild;u.replaceWith(...u.childNodes)}for(;(i=y.nextNode())!==null&&o.length<c;){if(i.nodeType===1){if(i.hasAttributes())for(let u of i.getAttributeNames())if(u.endsWith(fe)){let m=l[a++],_=i.getAttribute(u).split(b),L=/([.?@])?(.*)/.exec(m);o.push({type:1,index:r,name:L[2],strings:_,ctor:L[1]==="."?G:L[1]==="?"?X:L[1]==="@"?q:S}),i.removeAttribute(u)}else u.startsWith(b)&&(o.push({type:6,index:r}),i.removeAttribute(u));if(ve.test(i.tagName)){let u=i.textContent.split(b),m=u.length-1;if(m>0){i.textContent=H?H.emptyScript:"";for(let _=0;_<m;_++)i.append(u[_],R()),y.nextNode(),o.push({type:2,index:++r});i.append(u[m],R())}}}else if(i.nodeType===8)if(i.data===_e)o.push({type:2,index:r});else{let u=-1;for(;(u=i.data.indexOf(b,u+1))!==-1;)o.push({type:7,index:r}),u+=b.length-1}r++}}static createElement(t,e){let s=k.createElement("template");return s.innerHTML=t,s}};function A(n,t,e=n,s){if(t===w)return t;let i=s!==void 0?e._$Co?.[s]:e._$Cl,r=M(t)?void 0:t._$litDirective$;return i?.constructor!==r&&(i?._$AO?.(!1),r===void 0?i=void 0:(i=new r(n),i._$AT(n,e,s)),s!==void 0?(e._$Co??=[])[s]=i:e._$Cl=i),i!==void 0&&(t=A(n,i._$AS(n,t.values),i,s)),t}var V=class{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){let{el:{content:e},parts:s}=this._$AD,i=(t?.creationScope??k).importNode(e,!0);y.currentNode=i;let r=y.nextNode(),a=0,c=0,o=s[0];for(;o!==void 0;){if(a===o.index){let p;o.type===2?p=new N(r,r.nextSibling,this,t):o.type===1?p=new o.ctor(r,o.name,o.strings,this,t):o.type===6&&(p=new J(r,this,t)),this._$AV.push(p),o=s[++c]}a!==o?.index&&(r=y.nextNode(),a++)}return y.currentNode=k,i}p(t){let e=0;for(let s of this._$AV)s!==void 0&&(s.strings!==void 0?(s._$AI(t,s,e),e+=s.strings.length-2):s._$AI(t[e])),e++}},N=class n{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,s,i){this.type=2,this._$AH=h,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=s,this.options=i,this._$Cv=i?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode,e=this._$AM;return e!==void 0&&t?.nodeType===11&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=A(this,t,e),M(t)?t===h||t==null||t===""?(this._$AH!==h&&this._$AR(),this._$AH=h):t!==this._$AH&&t!==w&&this._(t):t._$litType$!==void 0?this.$(t):t.nodeType!==void 0?this.T(t):Le(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==h&&M(this._$AH)?this._$AA.nextSibling.data=t:this.T(k.createTextNode(t)),this._$AH=t}$(t){let{values:e,_$litType$:s}=t,i=typeof s=="number"?this._$AC(t):(s.el===void 0&&(s.el=j.createElement(be(s.h,s.h[0]),this.options)),s);if(this._$AH?._$AD===i)this._$AH.p(e);else{let r=new V(i,this),a=r.u(this.options);r.p(e),this.T(a),this._$AH=r}}_$AC(t){let e=me.get(t.strings);return e===void 0&&me.set(t.strings,e=new j(t)),e}k(t){Q(this._$AH)||(this._$AH=[],this._$AR());let e=this._$AH,s,i=0;for(let r of t)i===e.length?e.push(s=new n(this.O(R()),this.O(R()),this,this.options)):s=e[i],s._$AI(r),i++;i<e.length&&(this._$AR(s&&s._$AB.nextSibling,i),e.length=i)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){let s=le(t).nextSibling;le(t).remove(),t=s}}setConnected(t){this._$AM===void 0&&(this._$Cv=t,this._$AP?.(t))}},S=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,s,i,r){this.type=1,this._$AH=h,this._$AN=void 0,this.element=t,this.name=e,this._$AM=i,this.options=r,s.length>2||s[0]!==""||s[1]!==""?(this._$AH=Array(s.length-1).fill(new String),this.strings=s):this._$AH=h}_$AI(t,e=this,s,i){let r=this.strings,a=!1;if(r===void 0)t=A(this,t,e,0),a=!M(t)||t!==this._$AH&&t!==w,a&&(this._$AH=t);else{let c=t,o,p;for(t=r[0],o=0;o<r.length-1;o++)p=A(this,c[s+o],e,o),p===w&&(p=this._$AH[o]),a||=!M(p)||p!==this._$AH[o],p===h?t=h:t!==h&&(t+=(p??"")+r[o+1]),this._$AH[o]=p}a&&!i&&this.j(t)}j(t){t===h?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}},G=class extends S{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===h?void 0:t}},X=class extends S{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==h)}},q=class extends S{constructor(t,e,s,i,r){super(t,e,s,i,r),this.type=5}_$AI(t,e=this){if((t=A(this,t,e,0)??h)===w)return;let s=this._$AH,i=t===h&&s!==h||t.capture!==s.capture||t.once!==s.once||t.passive!==s.passive,r=t!==h&&(s===h||i);i&&this.element.removeEventListener(this.name,this,s),r&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}},J=class{constructor(t,e,s){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=s}get _$AU(){return this._$AM._$AU}_$AI(t){A(this,t)}};var De=Z.litHtmlPolyfillSupport;De?.(j,N),(Z.litHtmlVersions??=[]).push("3.3.3");var xe=(n,t,e)=>{let s=e?.renderBefore??t,i=s._$litPart$;if(i===void 0){let r=e?.renderBefore??null;s._$litPart$=i=new N(t.insertBefore(R(),r),r,void 0,e??{})}return i._$AI(n),i};var te=globalThis,x=class extends v{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){let e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=xe(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return w}};x._$litElement$=!0,x.finalized=!0,te.litElementHydrateSupport?.({LitElement:x});var Oe=te.litElementPolyfillSupport;Oe?.({LitElement:x});(te.litElementVersions??=[]).push("4.2.2");var He={address:"Schalten / Senden",state_address:"Status",brightness_address:"Helligkeit",brightness_state_address:"Helligkeit Status",color_temperature_address:"Farbtemperatur",color_temperature_state_address:"Farbtemperatur Status",color_address:"Farbe",color_state_address:"Farbe Status",move_long_address:"Auf/Ab",move_short_address:"Schritt/Stopp",stop_address:"Stopp",position_address:"Position",position_state_address:"Position Status",angle_address:"Lamelle",angle_state_address:"Lamelle Status",temperature_address:"Ist-Temperatur",target_temperature_address:"Soll-Temperatur",target_temperature_state_address:"Soll-Temperatur Status",setpoint_shift_address:"Sollwertverschiebung",setpoint_shift_state_address:"Sollwertverschiebung Status",operation_mode_address:"Betriebsart",operation_mode_state_address:"Betriebsart Status",on_off_address:"Ein/Aus",on_off_state_address:"Ein/Aus Status",address_temperature:"Temperatur",address_brightness_south:"Helligkeit S\xFCd",address_brightness_east:"Helligkeit Ost",address_brightness_west:"Helligkeit West",address_brightness_north:"Helligkeit Nord",address_wind_speed:"Windgeschwindigkeit",address_rain_alarm:"Regenalarm",address_frost_alarm:"Frostalarm",address_wind_alarm:"Windalarm",address_day_night:"Tag/Nacht",address_air_pressure:"Luftdruck",address_humidity:"Luftfeuchte"},Ie={address:"Switch / send",state_address:"State",brightness_address:"Brightness",brightness_state_address:"Brightness state",color_temperature_address:"Color temperature",color_temperature_state_address:"Color temperature state",color_address:"Color",color_state_address:"Color state",move_long_address:"Up/down",move_short_address:"Step/stop",stop_address:"Stop",position_address:"Position",position_state_address:"Position state",angle_address:"Slat angle",angle_state_address:"Slat angle state",temperature_address:"Current temperature",target_temperature_address:"Target temperature",target_temperature_state_address:"Target temperature state",setpoint_shift_address:"Setpoint shift",setpoint_shift_state_address:"Setpoint shift state",operation_mode_address:"Operation mode",operation_mode_state_address:"Operation mode state",on_off_address:"On/off",on_off_state_address:"On/off state",address_temperature:"Temperature",address_brightness_south:"Brightness south",address_brightness_east:"Brightness east",address_brightness_west:"Brightness west",address_brightness_north:"Brightness north",address_wind_speed:"Wind speed",address_rain_alarm:"Rain alarm",address_frost_alarm:"Frost alarm",address_wind_alarm:"Wind alarm",address_day_night:"Day/night",address_air_pressure:"Air pressure",address_humidity:"Humidity"},Ue={menu:"Men\xFC",loading:"Lade \u2026",noProject:"Noch kein Projekt importiert. Lade eine .knxproj-Datei hoch oder lies das Projekt aus dem KNX-Panel ein.",lastImport:n=>`Letzter Import: ${n}`,neverImported:"Noch nicht importiert",count:n=>`${n} Entities angelegt`,fromKnx:"Aus KNX-Panel einlesen",upload:"Projektdatei hochladen",staged:"Neue Projektversion geladen. Pr\xFCfe die \xC4nderungen und \xFCbernimm sie, oder verwirf sie.",discardProject:"Projektversion verwerfen",loaded:"Projekt eingelesen. Neue Entities sind unter \u201ENeu verf\xFCgbar\u201C zu finden.",passwordNeeded:"Das Projekt ist passwortgesch\xFCtzt.",password:"Projekt-Passwort",open:"\xD6ffnen",cancel:"Abbrechen",search:"Suchen nach Name, Adresse, Raum \u2026",groupBy:"Gruppieren",byRoom:"Nach Raum",byType:"Nach Typ",noRoom:"Ohne Raum",nothingFound:"Keine Entities f\xFCr diesen Filter.",selectGroup:n=>`Alle in ${n} ausw\xE4hlen`,create:n=>`${n} anlegen`,name:"Name",type:"Typ",suggestLight:"Klingt nach Licht",suggestLightTitle:"Der Name deutet auf eine Lampe hin. Als Licht anlegen.",unmappedHint:"F\xFCr diese Gruppenadressen wurde kein Entity-Typ erkannt. Sie werden nicht angelegt. Lege sie bei Bedarf von Hand in der KNX-YAML oder im KNX-Panel an.",willAdd:"Wird hinzugef\xFCgt",willChange:"Wird ge\xE4ndert",willRemove:"Wird entfernt",summary:(n,t,e)=>`+${n} hinzuf\xFCgen \xB7 ${t} \xE4ndern \xB7 \u2212${e} entfernen`,stillPending:n=>`${n} neu verf\xFCgbar, nicht ausgew\xE4hlt`,discard:"Verwerfen",apply:"\xDCbernehmen",applying:"\xDCbernehme \u2026",applied:n=>`\xDCbernommen: ${n.new??0} neu, ${n.changed??0} ge\xE4ndert, ${n.deleted??0} entfernt. KNX wurde neu geladen.`,willAdopt:"Wird aus deiner YAML \xFCbernommen",adoptCount:n=>`${n} \xFCbernehmen`,adopt:"In App \xFCbernehmen",undo:"R\xFCckg\xE4ngig",ownYaml:"deiner eigenen KNX-YAML",conflictInfo:(n,t,e)=>`Schon in deiner YAML: ${n} \u201E${t}\u201C (${e}). Wird nicht doppelt angelegt.`,gaInYaml:(n,t,e,s)=>`Die Gruppenadresse ${n} verwendet schon dein ${t} \u201E${e}\u201C (${s}). Nicht angelegt: \xFCbernimm es in die App, oder schalte die Entity ein, um sie trotzdem anzulegen.`,gaInApp:(n,t,e)=>`Die Gruppenadresse ${n} geh\xF6rt schon zu ${t} \u201E${e}\u201C in der App. Einschalten, um sie trotzdem anzulegen.`,adoptInfo:n=>`Wird mit deiner Konfiguration in die App \xFCbernommen und aus ${n} entfernt. Vorher wird eine Sicherung angelegt.`,notAdoptable:"Nicht automatisch \xFCbernehmbar, bitte in der YAML entfernen.",markExisting:"Schon vorhanden",existingTitle:"Diese Entity gibt es schon (z. B. in deiner YAML als anderer Typ). Nicht anlegen.",resetConfig:"Auf Projekt zur\xFCcksetzen",ownConfigTitle:"Nutzt deine \xFCbernommene Konfiguration. Zur\xFCcksetzen auf die Erkennung aus dem ETS-Projekt.",adoptFailed:n=>`\xDCbernahme aus deiner YAML nicht m\xF6glich: ${n}. Es wurde nichts ge\xE4ndert.`,adoptReasons:{not_a_list_item:"der Eintrag ist kein einfacher Listeneintrag (\u201E- name: \u2026\u201C)",flow_style:"der Eintrag steht in Kurzschreibweise ({ \u2026 })",outside_config:"die Datei liegt au\xDFerhalb des Konfigurationsordners",line_not_found:"die Datei hat sich ge\xE4ndert, bitte neu laden",verification:"nach dem Entfernen h\xE4tte sich mehr als dieser Eintrag ge\xE4ndert"},editAddresses:"Adressen bearbeiten",doneAddresses:"Fertig",addAddress:"Adresse hinzuf\xFCgen \u2026",removeAddress:n=>`${n} entfernen`,fromEts:"aus der ETS",etsValue:n=>`ETS: ${n||"keine"} \xB7 `,addedByHand:"von Hand hinzugef\xFCgt",reset:"zur\xFCcksetzen",invalidAddress:"Keine g\xFCltige Gruppenadresse (z. B. 1/2/3)",fixAddresses:"Ung\xFCltige Gruppenadresse korrigieren",fieldLabel:n=>He[n]??n,eyebrow:"ETS-Projekt",firstTitle:"Projekt eingelesen, noch nichts angelegt",firstDetail:"Alle erkannten Entities sind vorausgew\xE4hlt. Schalte ab, was du nicht brauchst, korrigiere Namen, Typen und Adressen und klicke dann auf \u201E\xDCbernehmen\u201C.",ownYamlTitle:n=>`${n} ${n===1?"Entity steht":"Entities stehen"} schon in deiner eigenen KNX-YAML`,ownYamlDetail:"Sie werden nicht doppelt angelegt. Du kannst sie mit deiner Konfiguration in die App \xFCbernehmen; deine Datei wird vorher gesichert.",adoptAll:n=>`Alle ${n} in die App \xFCbernehmen`,sources:{upload:"Datei-Upload",knx_project:"KNX-Panel",file:"Datei"},lastImportLine:(n,t)=>`Letzter Import ${n} \xB7 Quelle: ${t}`,stagedTitle:"Neue Projektversion geladen",stagedDetail:(n,t,e)=>`${n} neue ${n===1?"Entity":"Entities"} gefunden, ${t} ge\xE4ndert, ${e} nicht mehr im Projekt. Noch nichts \xFCbernommen.`,discardVersion:"Version verwerfen",stats:{active:["Angelegt","Entities"],pending:["Neu verf\xFCgbar","zum Hinzuf\xFCgen"],off:["Abgew\xE4hlt","nicht angelegt"],unmapped:["Ohne Typ","Gruppenadressen"]},statsSelected:["Ausgew\xE4hlt","werden angelegt"],moreFilters:"Weitere",roomCount:(n,t)=>`${n} von ${t} ausgew\xE4hlt`,allOn:"Alle anlegen",allOff:"Alle abw\xE4hlen",barCounts:{add:"hinzuf\xFCgen",change:"\xE4ndern",remove:"entfernen",adopt:"\xFCbernehmen"},showDetails:"Details anzeigen",hideDetails:"Details ausblenden",applyLong:"\xDCbernehmen und KNX neu laden",filters:{all:"Alle",active:"Angelegt",pending:"Neu verf\xFCgbar",off:"Abgew\xE4hlt",existing:"Schon vorhanden",issues:"Nicht m\xF6glich",gone:"Nicht mehr im Projekt",unmapped:"Ohne Typ"},status:{new:"Wird hinzugef\xFCgt",changed:"Wird ge\xE4ndert",retyped:"Typ wird ge\xE4ndert",unchanged:"Aktiv",kept:"Behalten",removed:"Wird entfernt",pending:"Neu verf\xFCgbar",deselected:"Abgew\xE4hlt",deselected_removed:"Wird entfernt",excluded:"Typ ausgeschlossen",duplicate:"Doppelt",invalid:"Ung\xFCltig",conflict:"Eigene YAML",ga_in_use:"GA schon belegt",existing:"Schon vorhanden",adopt:"Wird \xFCbernommen",own_config:"Aktiv \xB7 eigene Konfiguration"},reasons:{own_yaml:"Schon in deiner eigenen KNX-YAML definiert",ga_in_use:"Gruppenadresse schon verwendet",light:"GA schon von einem Licht belegt",unique_id:"Gleiche Gruppenadresse wie eine andere Entity"},domains:{switch:"Schalter",light:"Licht",binary_sensor:"Bin\xE4rsensor",sensor:"Sensor",time:"Uhrzeit",date:"Datum",datetime:"Datum/Uhrzeit",cover:"Rollladen/Jalousie",scene:"Szene",climate:"Klima",weather:"Wetter",text:"Text"},errors:{invalid_password:"Falsches oder fehlendes Projekt-Passwort.",invalid_project:"Keine lesbare ETS-Projektdatei.",no_knx_project:"Im KNX-Panel ist kein Projekt hochgeladen.",not_set_up:"KNX Project Sync ist nicht eingerichtet.",no_project:"Es wurde noch kein Projekt importiert."}},Fe={menu:"Menu",loading:"Loading \u2026",noProject:"No project imported yet. Upload a .knxproj file or read the project from the KNX panel.",lastImport:n=>`Last import: ${n}`,neverImported:"Not imported yet",count:n=>`${n} entities created`,fromKnx:"Read from KNX panel",upload:"Upload project file",staged:"New project version loaded. Review the changes and apply them, or discard them.",discardProject:"Discard project version",loaded:"Project loaded. New entities are listed under \u201CNewly available\u201D.",passwordNeeded:"The project is password protected.",password:"Project password",open:"Open",cancel:"Cancel",search:"Search name, address, room \u2026",groupBy:"Group by",byRoom:"By room",byType:"By type",noRoom:"No room",nothingFound:"No entities for this filter.",selectGroup:n=>`Select all in ${n}`,create:n=>`Create ${n}`,name:"Name",type:"Type",suggestLight:"Sounds like a light",suggestLightTitle:"The name suggests a lamp. Create it as a light.",unmappedHint:"No entity type was detected for these group addresses, so they are not created. Add them by hand in the KNX YAML or the KNX panel if needed.",willAdd:"Will be added",willChange:"Will be changed",willRemove:"Will be removed",summary:(n,t,e)=>`+${n} add \xB7 ${t} change \xB7 \u2212${e} remove`,stillPending:n=>`${n} newly available, not selected`,discard:"Discard",apply:"Apply",applying:"Applying \u2026",applied:n=>`Applied: ${n.new??0} new, ${n.changed??0} changed, ${n.deleted??0} removed. KNX was reloaded.`,willAdopt:"Taken over from your YAML",adoptCount:n=>`${n} take over`,adopt:"Take over into the app",undo:"Undo",ownYaml:"your own KNX YAML",conflictInfo:(n,t,e)=>`Already in your YAML: ${n} \u201C${t}\u201D (${e}). Not created twice.`,gaInYaml:(n,t,e,s)=>`Group address ${n} is already used by your ${t} \u201C${e}\u201D (${s}). Not created: take it over into the app, or switch the entity on to create it anyway.`,gaInApp:(n,t,e)=>`Group address ${n} already belongs to ${t} \u201C${e}\u201D in the app. Switch it on to create it anyway.`,adoptInfo:n=>`Taken over into the app with your configuration and removed from ${n}. A backup is made first.`,notAdoptable:"Cannot be taken over automatically, please remove it from the YAML.",markExisting:"Already exists",existingTitle:"This entity already exists (e.g. in your YAML as another type). Do not create it.",resetConfig:"Reset to project",ownConfigTitle:"Uses your taken-over configuration. Reset to what the ETS project detects.",adoptFailed:n=>`Could not take over from your YAML: ${n}. Nothing was changed.`,adoptReasons:{not_a_list_item:"the entry is not a plain list item (\u201C- name: \u2026\u201D)",flow_style:"the entry uses the short flow style ({ \u2026 })",outside_config:"the file is outside the configuration folder",line_not_found:"the file has changed, please reload",verification:"removing it would have changed more than this entry"},editAddresses:"Edit addresses",doneAddresses:"Done",addAddress:"Add address \u2026",removeAddress:n=>`Remove ${n}`,fromEts:"from ETS",etsValue:n=>`ETS: ${n||"none"} \xB7 `,addedByHand:"added by hand",reset:"reset",invalidAddress:"Not a valid group address (e.g. 1/2/3)",fixAddresses:"Fix the invalid group address",fieldLabel:n=>Ie[n]??n,eyebrow:"ETS project",firstTitle:"Project loaded, nothing created yet",firstDetail:"All detected entities are preselected. Switch off what you do not need, fix names, types and addresses, then click \u201CApply\u201D.",ownYamlTitle:n=>`${n} ${n===1?"entity is":"entities are"} already in your own KNX YAML`,ownYamlDetail:"They are not created twice. You can take them over into the app with your configuration; your file is backed up first.",adoptAll:n=>`Take all ${n} over into the app`,sources:{upload:"file upload",knx_project:"KNX panel",file:"file"},lastImportLine:(n,t)=>`Last import ${n} \xB7 Source: ${t}`,stagedTitle:"New project version loaded",stagedDetail:(n,t,e)=>`${n} new ${n===1?"entity":"entities"} found, ${t} changed, ${e} no longer in the project. Nothing applied yet.`,discardVersion:"Discard version",stats:{active:["Created","entities"],pending:["Newly available","to add"],off:["Deselected","not created"],unmapped:["No type","group addresses"]},statsSelected:["Selected","will be created"],moreFilters:"More",roomCount:(n,t)=>`${n} of ${t} selected`,allOn:"Create all",allOff:"Deselect all",barCounts:{add:"add",change:"change",remove:"remove",adopt:"take over"},showDetails:"Show details",hideDetails:"Hide details",applyLong:"Apply and reload KNX",filters:{all:"All",active:"Created",pending:"Newly available",off:"Deselected",existing:"Already exists",issues:"Not possible",gone:"No longer in project",unmapped:"No type"},status:{new:"Will be added",changed:"Will change",retyped:"Type changes",unchanged:"Active",kept:"Kept",removed:"Will be removed",pending:"Newly available",deselected:"Deselected",deselected_removed:"Will be removed",excluded:"Type excluded",duplicate:"Duplicate",invalid:"Invalid",conflict:"Own YAML",ga_in_use:"GA in use",existing:"Already exists",adopt:"Will be taken over",own_config:"Active \xB7 own configuration"},reasons:{own_yaml:"Already defined in your own KNX YAML",ga_in_use:"Group address already in use",light:"GA already used by a light",unique_id:"Same group address as another entity"},domains:{switch:"Switch",light:"Light",binary_sensor:"Binary sensor",sensor:"Sensor",time:"Time",date:"Date",datetime:"Date/time",cover:"Cover",scene:"Scene",climate:"Climate",weather:"Weather",text:"Text"},errors:{invalid_password:"Wrong or missing project password.",invalid_project:"Not a readable ETS project file.",no_knx_project:"No project is uploaded in the KNX panel.",not_set_up:"KNX Project Sync is not set up.",no_project:"No project has been imported yet."}},se={de:Ue,en:Fe};var $e=/^(\d{1,2}\/\d{1,2}\/\d{1,3}|\d{1,2}\/\d{1,4}|\d{1,5})$/,we=new Set(["new","changed","unchanged","kept"]),Ae=new Set(["excluded","duplicate","invalid","conflict","removed","existing"]);var I=n=>Ae.has(n.status)&&!((n.status==="conflict"||n.status==="duplicate")&&n.conflict_with&&n.conflict_with.kind!=="unique_id"),ye=(n,t)=>{switch(t){case"all":return!0;case"active":return we.has(n.status);case"pending":return n.status==="pending";case"existing":return n.status==="existing";case"off":return n.status==="deselected";case"issues":return["excluded","duplicate","invalid","conflict"].includes(n.status);case"gone":return!n.in_project;default:return!1}},U=n=>{let t={};for(let[e,s]of Object.entries(n)){let i={};(s.enabled===!0||s.enabled===!1)&&(i.enabled=s.enabled),s.domain&&(i.domain=s.domain),s.name&&s.name.trim()&&(i.name=s.name.trim()),s.existing&&(i.existing=!0),s.adopt&&(i.adopt=!0),s.config&&(i.config=s.config),s.addresses&&Object.keys(s.addresses).length&&(i.addresses=s.addresses),Object.keys(i).length&&(t[e]=i)}return t},Ke=(n,t)=>JSON.stringify(ke(U(n)))===JSON.stringify(ke(U(t))),ke=n=>Object.fromEntries(Object.entries(n).sort(([t],[e])=>t.localeCompare(e))),P=class extends x{constructor(){super(...arguments);this.narrow=!1;this._data=null;this._draft={};this._search="";this._filter="all";this._group="room";this._busy=null;this._error=null;this._message=null;this._passwordFor=null;this._showChanges=!1;this._loaded=!1;this._request=0;this._editing=new Set}get t(){let e=(this.hass?.locale?.language||this.hass?.language||"en").slice(0,2);return se[e]??se.en}updated(e){if(e.has("hass")&&this.hass&&!this._loaded){this._loaded=!0,this._refresh(void 0,!0);try{let s=JSON.parse(localStorage.getItem("knx-project-sync-view")??"{}");(s.group==="room"||s.group==="domain")&&(this._group=s.group)}catch{}}}async _refresh(e,s=!1){let i=++this._request;try{let r={type:"knx_project_sync/plan"};e&&(r.selection=U(e));let a=await this.hass.callWS(r);if(i!==this._request)return;this._data=a,s&&(this._draft=structuredClone(a.stored_selection??{})),this._error=null}catch(r){i===this._request&&(this._error=this._errorText(r))}}_scheduleRefresh(){window.clearTimeout(this._timer),this._timer=window.setTimeout(()=>this._refresh(this._draft),250)}_errorText(e){let s=e;return s.code==="adopt_failed"?this.t.adoptFailed(this.t.adoptReasons[s.message??""]??s.message??""):s.code&&this.t.errors[s.code]||s.message||String(e)}async _loadKnxProject(){await this._run("load",async()=>{await this.hass.callWS({type:"knx_project_sync/load_project",source:"knx_project"}),await this._refresh(this._draft),this._message=this.t.loaded})}async _upload(e,s){await this._run("load",async()=>{let i=new FormData;i.append("file",e);let r=await this.hass.fetchWithAuth("/api/file_upload",{method:"POST",body:i});if(!r.ok)throw new Error(`${r.status} ${await r.text()}`);let{file_id:a}=await r.json();try{await this.hass.callWS({type:"knx_project_sync/load_project",source:"upload",file_id:a,...s?{password:s}:{}})}catch(c){throw c.code==="invalid_password"&&(this._passwordFor=e),c}this._passwordFor=null,await this._refresh(this._draft),this._message=this.t.loaded})}async _discard(){await this._run("discard",async()=>{this._data?.staged&&await this.hass.callWS({type:"knx_project_sync/discard"}),this._showChanges=!1,await this._refresh(void 0,!0)})}async _apply(){await this._run("apply",async()=>{let e=await this.hass.callWS({type:"knx_project_sync/apply",selection:U(this._draft)});this._showChanges=!1,await this._refresh(void 0,!0),this._message=this.t.applied(e)})}async _run(e,s){this._busy=e,this._error=null,this._message=null;try{await s()}catch(i){this._error=this._errorText(i)}finally{this._busy=null}}_choose(e,s){let i={...this._draft[e]??{},...s};this._draft={...this._draft,[e]:i},this._scheduleRefresh()}_checked(e){let s=this._draft[e.key]?.enabled;return s===!0||s===!1?s&&!I(e):we.has(e.status)}_toggleMany(e,s){let i={...this._draft};for(let r of e)I(r)||(i[r.key]={...i[r.key]??{},enabled:s});this._draft=i,this._scheduleRefresh()}get _dirty(){return this._data?this._data.staged||!Ke(this._draft,this._data.stored_selection??{})||!!this._data.has_changes:!1}_visible(){let e=this._search.trim().toLowerCase();return(this._data?.entities??[]).filter(s=>ye(s,this._filter)?e?[s.name,s.ets_name,s.room,s.key,s.entity_id,s.domain,...s.addresses.map(r=>r.address)].filter(Boolean).join(" ").toLowerCase().includes(e):!0:!1)}render(){let e=this.t,s=this._data;return d`
      <header class="toolbar">
        ${this.narrow?d`<button class="icon-button" aria-label=${e.menu} @click=${this._toggleMenu}>${f(g.menu)}</button>`:d`<div class="app-icon">${f(g.home,20)}</div>`}
        <h1 class="app-title">KNX Project Sync</h1>
        <span class="grow"></span>
        ${s?.has_knx_project?d`<button
              class="secondary tool"
              aria-label=${e.fromKnx}
              title=${e.fromKnx}
              ?disabled=${!!this._busy}
              @click=${this._loadKnxProject}
            >
              ${f(g.refresh,18)}<span class="btn-label">${e.fromKnx}</span>
            </button>`:h}
        <label
          class="button primary tool ${this._busy?"disabled":""}"
          title=${e.upload}
        >
          ${f(g.upload,18)}<span class="btn-label">${e.upload}</span>
          <input
            type="file"
            accept=".knxproj"
            class="visually-hidden"
            ?disabled=${!!this._busy}
            @change=${i=>{let r=i.target,a=r.files?.[0];r.value="",a&&this._upload(a)}}
          />
        </label>
      </header>
      <main class="content">
        ${this._renderProject()}
        ${this._error?d`<div class="alert error" role="alert">${this._error}</div>`:h}
        ${this._message?d`<div class="alert info" role="status">${this._message}</div>`:h}
        ${this._passwordFor?this._renderPassword():h}
        ${s?s.project?d`${this._renderStaged()} ${this._renderStats()} ${this._renderSearch()}
              ${this._filter==="unmapped"?this._renderUnmapped():this._renderGroups()}`:d`<div class="empty">${e.noProject}</div>`:d`<div class="empty">${e.loading}</div>`}
      </main>
      ${s?.project&&this._dirty?this._renderBar():h}
    `}_renderProject(){let e=this.t,s=this._data,i=s?.last_import,r=i?new Date(i.time).toLocaleString(this.hass.language,{dateStyle:"medium",timeStyle:"short"}):null;return d`<section class="project">
      <div class="eyebrow">${e.eyebrow}</div>
      <h2>${s?.project??"\u2013"}</h2>
      <div class="sub">${r?e.lastImportLine(r,e.sources[i.source]??i.source):e.neverImported}</div>
    </section>`}_renderStaged(){let e=this.t;if(!this._data)return h;let s=new Set,i=this._data.entities.filter(l=>{let u=l.conflict_with;if(l.status!=="conflict"||!u?.adoptable||this._draft[l.key]?.adopt)return!1;let m=`${u.file}:${u.line}`;return s.has(m)?!1:(s.add(m),!0)}),r=i.length?d`<section class="staged notice">
          <div class="staged-icon">${f(g.file,20)}</div>
          <div class="grow">
            <div class="staged-title">${e.ownYamlTitle(i.length)}</div>
            <div>${e.ownYamlDetail}</div>
          </div>
          <button class="secondary" ?disabled=${!!this._busy} @click=${()=>this._adoptAll(i)}>
            ${e.adoptAll(i.length)}
          </button>
        </section>`:h;if(!this._data.last_import&&!this._data.staged)return d`<section class="staged notice">
          <div class="staged-icon">${f(g.light,20)}</div>
          <div class="grow">
            <div class="staged-title">${e.firstTitle}</div>
            <div>${e.firstDetail}</div>
          </div>
        </section>
        ${r}`;if(!this._data.staged)return r;let a=this._data.entities,c=a.filter(l=>l.status==="pending").length,o=a.filter(l=>l.status==="changed").length,p=a.filter(l=>!l.in_project).length;return d`<section class="staged">
      <div class="staged-icon">${f(g.file,20)}</div>
      <div class="grow">
        <div class="staged-title">${e.stagedTitle}</div>
        <div>${e.stagedDetail(c,o,p)}</div>
      </div>
      <button class="text" ?disabled=${!!this._busy} @click=${this._discard}>${e.discardVersion}</button>
    </section>
    ${r}`}_adoptAll(e){let s={...this._draft};for(let i of e)s[i.key]={...s[i.key]??{},adopt:!0};this._draft=s,this._scheduleRefresh()}_count(e){return e==="unmapped"?this._data?.unmapped.length??0:(this._data?.entities??[]).filter(s=>ye(s,e)).length}_setFilter(e){this._filter=this._filter===e?"all":e}_renderStats(){let e=this.t,s=["active","pending","off","unmapped"],i=["existing","issues","gone"].filter(r=>this._count(r)>0||this._filter===r);return d`<section class="stats">
        ${s.map(r=>{let[a,c]=r==="active"&&!this._data?.last_import?e.statsSelected:e.stats[r],o=this._count(r);return d`<button
            class="stat ${this._filter===r?"active":""} ${r==="pending"&&o?"accent":""}"
            aria-pressed=${this._filter===r}
            @click=${()=>this._setFilter(r)}
          >
            <span class="stat-label">${a}</span>
            <span class="stat-value"><strong>${o}</strong><span>${c}</span></span>
          </button>`})}
      </section>
      ${i.length?d`<div class="chips" role="group" aria-label=${e.moreFilters}>
            ${i.map(r=>d`<button class="chip ${this._filter===r?"active":""}" aria-pressed=${this._filter===r} @click=${()=>this._setFilter(r)}>
                ${e.filters[r]} <span class="n">${this._count(r)}</span>
              </button>`)}
          </div>`:h}`}_renderSearch(){let e=this.t,s=i=>{this._group=i;try{localStorage.setItem("knx-project-sync-view",JSON.stringify({group:i}))}catch{}};return d`<section class="search-row">
      <label class="search">
        ${f(g.search,18)}
        <input
          type="search"
          aria-label=${e.search}
          placeholder=${e.search}
          .value=${this._search}
          @input=${i=>this._search=i.target.value}
        />
      </label>
      <div class="segmented" role="group" aria-label=${e.groupBy}>
        ${["room","domain"].map(i=>d`<button aria-pressed=${this._group===i} class=${this._group===i?"on":""} @click=${()=>s(i)}>
            ${i==="room"?e.byRoom:e.byType}
          </button>`)}
      </div>
    </section>`}_renderGroups(){let e=this.t,s=this._visible();if(!s.length)return d`<div class="empty">${e.nothingFound}</div>`;let i=new Map;for(let a of s){let c=this._group==="room"?a.room||e.noRoom:e.domains[a.domain]??a.domain;i.set(c,[...i.get(c)??[],a])}let r=[...i.entries()].sort(([a],[c])=>a===e.noRoom?1:c===e.noRoom?-1:a.localeCompare(c,this.hass.language));return d`${r.map(([a,c])=>{let o=c.filter(m=>!I(m)),p=c.filter(m=>this._checked(m)).length,l=o.length>0&&o.every(m=>this._checked(m)),u=c.length?Math.round(p/c.length*100):0;return d`<section class="room">
        <div class="room-head">
          <h3>${a}</h3>
          <span class="sub">${e.roomCount(p,c.length)}</span>
          <div class="progress" role="progressbar" aria-valuenow=${u} aria-valuemin="0" aria-valuemax="100" aria-label=${e.roomCount(p,c.length)}>
            <div style="width: ${u}%"></div>
          </div>
          <button class="secondary small" ?disabled=${!o.length} @click=${()=>this._toggleMany(o,!l)}>
            ${l?e.allOff:e.allOn}
          </button>
        </div>
        ${c.map(m=>this._renderRow(m))}
      </section>`})}`}_renderRow(e){let s=this.t,i=this._draft[e.key]??{},r=I(e),a=this._checked(e),c=i.domain||e.detected_domain,o=e.adopt?"adopt":e.status,p=e.ets_name??e.key;return d`<div class="row ${a?"":"off"} ${e.status==="pending"?"pending":""}">
      <button
        class="toggle ${a?"on":""}"
        role="switch"
        aria-checked=${a}
        aria-label=${s.create(p)}
        ?disabled=${r}
        @click=${()=>this._choose(e.key,{enabled:!a})}
      >
        <span></span>
      </button>
      <div class="tile ${We(e.domain)}">${f(Be[e.domain]??g.generic,20)}</div>
      <div class="main">
        <label class="name">
          <input
            type="text"
            .value=${i.name??""}
            placeholder=${p}
            aria-label=${s.name}
            ?disabled=${!e.in_project}
            @change=${l=>this._choose(e.key,{name:l.target.value})}
          />
          ${e.in_project?f(g.pencil,15):h}
        </label>
        <div class="meta">
          ${e.addresses.map(l=>d`<code class=${e.project_addresses?.[l.field]===l.address?"":"edited"} title=${s.fieldLabel(l.field)}
                >${l.address}</code
              >`)}
          ${e.in_project&&e.address_fields?.length?d`<button
                class="link edit ${this._editing.has(e.key)?"":"mark"}"
                aria-expanded=${this._editing.has(e.key)}
                @click=${()=>this._toggleEditing(e.key)}
              >
                ${this._editing.has(e.key)?s.doneAddresses:s.editAddresses}
              </button>`:h}
          ${this._group==="domain"&&e.room?d`<span>${e.room}</span>`:h}
          ${e.entity_id?d`<a href="#" @click=${l=>this._moreInfo(l,e.entity_id)}>${e.entity_id}</a>`:h}
        </div>
      </div>
      <div class="type">
        ${e.domains.length>1?d`<div class="segmented small" role="group" aria-label=${s.type}>
              ${e.domains.map(l=>d`<button
                  class=${l===c?"on":""}
                  aria-pressed=${l===c}
                  ?disabled=${r}
                  @click=${()=>this._choose(e.key,{domain:l})}
                >
                  ${s.domains[l]??l}
                </button>`)}
            </div>`:d`<span class="domain">${s.domains[e.domain]??e.domain}</span>`}
        ${e.suggest_light&&c==="switch"&&!r?d`<button class="hint" title=${s.suggestLightTitle} @click=${()=>this._choose(e.key,{domain:"light"})}>
              ${f(g.light,14)} ${s.suggestLight}
            </button>`:h}
      </div>
      <div class="status">
        <span class="pill ${o}">${this._statusLabel(e)}</span>
        ${e.reason&&r&&!e.conflict_with?d`<span class="reason" title=${e.reason}>${this._reasonLabel(e)}</span>`:h}
        ${this._renderActions(e,i)}
      </div>
      ${e.conflict_with?this._renderConflict(e,i):h}
      ${this._editing.has(e.key)?this._renderAddresses(e,i):h}
    </div>`}_toggleEditing(e){let s=new Set(this._editing);s.has(e)?s.delete(e):s.add(e),this._editing=s}_address(e,s,i){let r=s.addresses??{};return i in r?r[i]??null:e.addresses.find(a=>a.field===i)?.address??null}_setAddress(e,s,i){let r={...this._draft[e.key]?.addresses??{}};i===void 0?delete r[s]:r[s]=i,this._choose(e.key,{addresses:Object.keys(r).length?r:null})}_renderAddresses(e,s){let i=this.t,r=s.addresses??{},a=e.address_fields.filter(o=>this._address(e,s,o)!==null||o in r),c=e.address_fields.filter(o=>!a.includes(o));return d`<div class="drawer">
      ${a.map(o=>{let p=this._address(e,s,o)??"",l=e.project_addresses[o],u=p===""||$e.test(p),m=`ga-${e.key}-${o}`;return d`<div class="addr">
          <label for=${m}>${i.fieldLabel(o)}</label>
          <input
            id=${m}
            type="text"
            inputmode="numeric"
            autocomplete="off"
            spellcheck="false"
            class=${u?"":"invalid"}
            aria-invalid=${!u}
            .value=${p}
            placeholder=${l??"1/2/3"}
            @change=${_=>this._setAddress(e,o,_.target.value.trim())}
          />
          <span class="addr-note">
            ${u?l===void 0?i.addedByHand:p===l?i.fromEts:d`${i.etsValue(l)}
                      <button class="link" @click=${()=>this._setAddress(e,o,void 0)}>${i.reset}</button>`:d`<span class="error-text">${i.invalidAddress}</span>`}
          </span>
          <button
            class="icon-button small"
            aria-label=${i.removeAddress(i.fieldLabel(o))}
            title=${i.removeAddress(i.fieldLabel(o))}
            @click=${()=>this._setAddress(e,o,l===void 0?void 0:null)}
          >
            ${f(g.close,16)}
          </button>
        </div>`})}
      ${c.length?d`<select
            aria-label=${i.addAddress}
            @change=${o=>{let p=o.target;p.value&&this._setAddress(e,p.value,""),p.value=""}}
          >
            <option value="">${i.addAddress}</option>
            ${c.map(o=>d`<option value=${o}>${i.fieldLabel(o)}</option>`)}
          </select>`:h}
    </div>`}get _invalidAddresses(){return Object.values(this._draft).some(e=>Object.values(e.addresses??{}).some(s=>s!==null&&s!==""&&!$e.test(s)))}_renderConflict(e,s){let i=this.t,r=e.conflict_with,a=r.file?`${r.file}${r.line?`:${r.line}`:""}`:i.ownYaml;return d`<div class="drawer conflict-box">
      <span class="grow">
        ${e.adopt?i.adoptInfo(a):r.kind==="app"?i.gaInApp(r.address??"",i.domains[r.domain]??r.domain,r.name??""):r.kind==="address"?i.gaInYaml(r.address??"",i.domains[r.domain]??r.domain,r.name??"",a):i.conflictInfo(i.domains[r.domain]??r.domain,r.name??"",a)}
      </span>
      ${s.adopt?d`<button class="text" @click=${()=>this._choose(e.key,{adopt:null})}>${i.undo}</button>`:r.kind==="app"?h:r.adoptable?d`<button class="secondary small" @click=${()=>this._choose(e.key,{adopt:!0})}>${i.adopt}</button>`:d`<span class="sub">${i.notAdoptable}</span>`}
    </div>`}_renderActions(e,s){let i=this.t;return e.in_project?e.status==="existing"||s.existing?d`<button class="link" @click=${()=>this._choose(e.key,{existing:null})}>${i.undo}</button>`:e.own_config&&s.config?d`<button class="link" title=${i.ownConfigTitle} @click=${()=>this._choose(e.key,{config:null,domain:null})}>
        ${i.resetConfig}
      </button>`:Ae.has(e.status)||e.adopt?h:d`<button class="link mark" title=${i.existingTitle} @click=${()=>this._choose(e.key,{existing:!0})}>
      ${i.markExisting}
    </button>`:h}_statusLabel(e){let s=this.t;return e.adopt?s.status.adopt:e.reason==="ga_in_use"?s.status.ga_in_use:e.own_config&&e.status==="unchanged"?s.status.own_config:e.status==="deselected"&&e.entity_id?s.status.deselected_removed:e.status==="changed"&&e.previous_domain&&e.previous_domain!==e.domain?s.status.retyped:s.status[e.status]??e.status}_reasonLabel(e){let s=this.t;return e.reason==="ga_in_use"?s.reasons.ga_in_use:e.status==="conflict"?s.reasons.own_yaml:e.status==="duplicate"?e.reason==="light"?s.reasons.light:s.reasons.unique_id:e.reason??""}_renderPassword(){let e=this.t;return d`<form class="alert warn" @submit=${i=>{i.preventDefault();let r=this.renderRoot.querySelector("#password");this._passwordFor&&r&&this._upload(this._passwordFor,r.value)}}>
      <label for="password" class="grow">${e.passwordNeeded}</label>
      <input id="password" type="password" autocomplete="off" placeholder=${e.password} />
      <button type="submit" class="primary" ?disabled=${!!this._busy}>${e.open}</button>
      <button type="button" class="text" @click=${()=>this._passwordFor=null}>${e.cancel}</button>
    </form>`}_renderUnmapped(){let e=this.t,s=this._search.trim().toLowerCase(),i=(this._data?.unmapped??[]).filter(r=>!s||`${r.address} ${r.name} ${r.dpt??""}`.toLowerCase().includes(s));return d`<p class="sub">${e.unmappedHint}</p>
      <section class="room">
        ${i.map(r=>d`<div class="row unmapped">
            <code>${r.address}</code>
            <div class="main">${r.name}</div>
            <span class="domain">${r.dpt?`DPT ${r.dpt}`:"\u2013"}</span>
          </div>`)}
      </section>`}_renderBar(){let e=this.t,s=this._data?.entities??[],i=s.filter(p=>p.status==="new"&&!p.adopt),r=s.filter(p=>p.adopt),a=s.filter(p=>p.status==="changed"),c=s.filter(p=>p.status==="removed"||(p.status==="deselected"||p.status==="existing")&&p.entity_id),o=[["add",e.willAdd,i],["change",e.willChange,a],["remove",e.willRemove,c],["adopt",e.willAdopt,r]];return d`<div class="bar-wrap">
      <div class="bar">
        ${this._showChanges?d`<div class="changes">
              ${o.map(([,p,l])=>l.length?d`<div>
                      <strong>${p}</strong>
                      <ul>
                        ${l.map(u=>d`<li>${u.name??u.key} <span class="dim">(${e.domains[u.domain]??u.domain})</span></li>`)}
                      </ul>
                    </div>`:h)}
            </div>`:h}
        <div class="bar-main">
          <div class="counts">
            ${o.map(([p,,l])=>p==="adopt"&&!l.length?h:d`<span class="count"><i class="dot ${p}"></i><strong>${l.length}</strong> ${e.barCounts[p]}</span>`)}
            <button class="link light" aria-expanded=${this._showChanges} @click=${()=>this._showChanges=!this._showChanges}>
              ${this._showChanges?e.hideDetails:e.showDetails}
            </button>
          </div>
          <div class="bar-actions">
            ${this._invalidAddresses?d`<span class="error-text">${e.fixAddresses}</span>`:h}
            <button class="outline" ?disabled=${!!this._busy} @click=${this._discard}>${e.discard}</button>
            <button class="primary" ?disabled=${!!this._busy||this._invalidAddresses} @click=${this._apply}>
              ${this._busy==="apply"?e.applying:d`<span class="long">${e.applyLong}</span><span class="short">${e.apply}</span>`}
            </button>
          </div>
        </div>
      </div>
    </div>`}_toggleMenu(){this.dispatchEvent(new CustomEvent("hass-toggle-menu",{bubbles:!0,composed:!0}))}_moreInfo(e,s){e.preventDefault(),this.dispatchEvent(new CustomEvent("hass-more-info",{detail:{entityId:s},bubbles:!0,composed:!0}))}};P.properties={hass:{attribute:!1},narrow:{type:Boolean},_data:{state:!0},_draft:{state:!0},_search:{state:!0},_filter:{state:!0},_group:{state:!0},_busy:{state:!0},_error:{state:!0},_message:{state:!0},_passwordFor:{state:!0},_showChanges:{state:!0},_editing:{state:!0}},P.styles=K`
    :host {
      --kps-accent: var(--primary-color, #0a6cdb);
      --kps-on-accent: var(--text-primary-color, #fff);
      --kps-ground: var(--primary-background-color, #f4f5f7);
      --kps-surface: var(--card-background-color, #fff);
      --kps-text: var(--primary-text-color, #15171a);
      --kps-muted: var(--secondary-text-color, #5b6270);
      --kps-line: var(--divider-color, rgba(0, 0, 0, 0.12));
      --kps-soft: color-mix(in srgb, var(--kps-text) 6%, transparent);
      --kps-radius: var(--ha-card-border-radius, 16px);
      --kps-success: var(--success-color, #1e9e56);
      --kps-warning: var(--warning-color, #e08600);
      --kps-error: var(--error-color, #d93025);
      --kps-amber: #e8a200;
      --kps-purple: #7b5cd6;
      display: block;
      min-height: 100vh;
      background: var(--kps-ground);
      color: var(--kps-text);
      font-family: var(--ha-font-family-body, Inter, Roboto, system-ui, sans-serif);
      -webkit-font-smoothing: antialiased;
    }
    * {
      box-sizing: border-box;
    }
    h1,
    h2,
    h3 {
      margin: 0;
    }
    .grow {
      flex: 1 1 auto;
      min-width: 0;
    }
    .visually-hidden {
      position: absolute;
      width: 1px;
      height: 1px;
      overflow: hidden;
      clip: rect(0 0 0 0);
      white-space: nowrap;
    }
    svg {
      flex: none;
    }

    /* ---------- controls */
    button,
    .button {
      font: inherit;
      font-size: 14px;
      font-weight: 500;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      height: 40px;
      padding: 0 16px;
      border-radius: 10px;
      border: 1px solid transparent;
      background: none;
      color: var(--kps-text);
      cursor: pointer;
      white-space: nowrap;
    }
    button:disabled,
    .button.disabled {
      opacity: 0.45;
      cursor: default;
    }
    button.primary,
    .button.primary {
      background: var(--kps-accent);
      color: var(--kps-on-accent);
      font-weight: 600;
    }
    button.secondary {
      background: var(--kps-surface);
      border-color: var(--kps-line);
    }
    button.small {
      height: 32px;
      padding: 0 12px;
      font-size: 13px;
      border-radius: 8px;
    }
    button.text {
      color: inherit;
      padding: 0 12px;
    }
    .short {
      display: none;
    }
    .icon-button {
      width: 44px;
      height: 44px;
      padding: 0;
      border-radius: 10px;
    }
    .icon-button.small {
      width: 32px;
      height: 32px;
      color: var(--kps-muted);
    }
    button.link {
      height: auto;
      padding: 2px 0;
      border-radius: 4px;
      font-size: 12px;
      color: var(--kps-accent);
    }
    input[type="text"],
    input[type="password"],
    select {
      font: inherit;
      font-size: 14px;
      color: var(--kps-text);
      background: var(--kps-surface);
      border: 1px solid var(--kps-line);
      border-radius: 8px;
      height: 36px;
      padding: 0 10px;
      min-width: 0;
    }
    :focus-visible {
      outline: 2px solid var(--kps-accent);
      outline-offset: 2px;
    }
    .sub {
      color: var(--kps-muted);
      font-size: 14px;
    }
    code {
      font-family: var(--ha-font-family-code, "JetBrains Mono", ui-monospace, monospace);
      font-size: 12px;
      background: var(--kps-soft);
      border-radius: 6px;
      padding: 2px 7px;
    }
    code.edited {
      background: color-mix(in srgb, var(--kps-warning) 18%, transparent);
      box-shadow: inset 0 0 0 1px var(--kps-warning);
    }

    /* ---------- toolbar */
    .toolbar {
      position: sticky;
      top: 0;
      z-index: 5;
      display: flex;
      align-items: center;
      gap: 12px;
      height: var(--header-height, 64px);
      padding: 0 24px;
      background: var(--kps-surface);
      border-bottom: 1px solid var(--kps-line);
    }
    .app-icon {
      width: 34px;
      height: 34px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--kps-accent);
      color: var(--kps-on-accent);
    }
    .app-title {
      font-size: 18px;
      font-weight: 600;
      letter-spacing: -0.01em;
    }

    /* ---------- content */
    .content {
      max-width: 1120px;
      margin: 0 auto;
      padding: 32px 24px 24px;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    .project {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .eyebrow {
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--kps-muted);
    }
    .project h2 {
      font-size: 32px;
      font-weight: 700;
      letter-spacing: -0.02em;
    }
    .alert {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 10px;
      padding: 12px 16px;
      border-radius: 12px;
      background: var(--kps-surface);
      border: 1px solid var(--kps-line);
    }
    .alert.error {
      border-color: var(--kps-error);
      color: var(--kps-error);
    }
    .alert.info {
      border-color: var(--kps-accent);
    }
    .staged {
      display: flex;
      align-items: center;
      gap: 14px;
      padding: 14px 18px;
      border-radius: 14px;
      background: color-mix(in srgb, var(--kps-warning) 12%, var(--kps-surface));
      border: 1px solid color-mix(in srgb, var(--kps-warning) 40%, transparent);
      font-size: 14px;
    }
    .staged > .grow {
      flex: 1 1 0;
    }
    .staged.notice {
      background: color-mix(in srgb, var(--kps-accent) 8%, var(--kps-surface));
      border-color: color-mix(in srgb, var(--kps-accent) 35%, transparent);
    }
    .staged.notice .staged-icon {
      background: color-mix(in srgb, var(--kps-accent) 18%, transparent);
      color: var(--kps-accent);
    }
    .staged-icon {
      width: 36px;
      height: 36px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: color-mix(in srgb, var(--kps-warning) 22%, transparent);
      color: var(--kps-warning);
    }
    .staged-title {
      font-size: 15px;
      font-weight: 600;
      margin-bottom: 2px;
    }
    .stats {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 16px;
    }
    .stat {
      height: auto;
      flex-direction: column;
      align-items: flex-start;
      justify-content: flex-start;
      gap: 6px;
      padding: 16px 18px;
      background: var(--kps-surface);
      border: 1px solid var(--kps-line);
      border-radius: 14px;
      text-align: left;
      white-space: normal;
    }
    .stat.accent {
      border-color: var(--kps-accent);
    }
    .stat.active {
      box-shadow: inset 0 0 0 2px var(--kps-accent);
      border-color: var(--kps-accent);
    }
    .stat-label {
      font-size: 13px;
      color: var(--kps-muted);
    }
    .stat-value {
      display: flex;
      align-items: baseline;
      gap: 8px;
      font-size: 13px;
      color: var(--kps-muted);
    }
    .stat-value strong {
      font-size: 28px;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: var(--kps-text);
    }
    .stat.accent strong {
      color: var(--kps-accent);
    }
    .chips {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: -8px;
    }
    .chip {
      height: 32px;
      padding: 0 12px;
      border-radius: 16px;
      border-color: var(--kps-line);
      background: var(--kps-surface);
      font-size: 13px;
    }
    .chip.active {
      background: var(--kps-text);
      color: var(--kps-surface);
    }
    .chip .n {
      opacity: 0.7;
    }
    .search-row {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }
    .search {
      flex: 1 1 200px;
      display: flex;
      align-items: center;
      gap: 10px;
      height: 44px;
      padding: 0 14px;
      background: var(--kps-surface);
      border: 1px solid var(--kps-line);
      border-radius: 12px;
      color: var(--kps-muted);
    }
    .search:focus-within {
      border-color: var(--kps-accent);
    }
    .search input {
      font: inherit;
      font-size: 15px;
      flex: 1;
      min-width: 0;
      border: none;
      outline: none;
      background: transparent;
      color: var(--kps-text);
    }
    .segmented {
      display: inline-flex;
      gap: 4px;
      padding: 4px;
      border-radius: 12px;
      background: var(--kps-soft);
    }
    .segmented button {
      height: 36px;
      padding: 0 14px;
      border-radius: 9px;
      color: var(--kps-muted);
    }
    .segmented button.on {
      background: var(--kps-surface);
      color: var(--kps-text);
      font-weight: 600;
      box-shadow: 0 1px 2px rgba(16, 24, 40, 0.12);
    }
    .segmented.small {
      padding: 3px;
      gap: 3px;
      border-radius: 10px;
    }
    .segmented.small button {
      height: 32px;
      padding: 0 12px;
      font-size: 13px;
      border-radius: 8px;
    }

    /* ---------- rooms and rows */
    .room {
      background: var(--kps-surface);
      border: 1px solid var(--ha-card-border-color, var(--kps-line));
      border-radius: var(--kps-radius);
      box-shadow: var(--ha-card-box-shadow, 0 1px 2px rgba(16, 24, 40, 0.04));
      overflow: hidden;
    }
    .room-head {
      display: flex;
      align-items: center;
      gap: 14px;
      padding: 14px 20px;
      flex-wrap: wrap;
    }
    .room-head h3 {
      font-size: 17px;
      font-weight: 600;
      flex: 1 1 auto;
    }
    .room-head .sub {
      font-size: 13px;
    }
    .progress {
      width: 96px;
      height: 6px;
      border-radius: 3px;
      background: var(--kps-soft);
      overflow: hidden;
    }
    .progress div {
      height: 100%;
      border-radius: 3px;
      background: var(--kps-accent);
      transition: width 0.2s;
    }
    .row {
      display: grid;
      grid-template-columns: 48px 40px minmax(0, 1fr) 210px 170px;
      align-items: center;
      gap: 10px 16px;
      padding: 14px 20px;
      border-top: 1px solid var(--kps-line);
    }
    .row.pending {
      background: color-mix(in srgb, var(--kps-accent) 5%, transparent);
    }
    .row.off .tile,
    .row.off .main {
      opacity: 0.6;
    }
    .row.unmapped {
      grid-template-columns: 90px minmax(0, 1fr) auto;
    }
    .toggle {
      width: 44px;
      height: 26px;
      padding: 3px;
      border-radius: 13px;
      background: color-mix(in srgb, var(--kps-text) 24%, transparent);
      justify-content: flex-start;
      transition: background 0.15s;
    }
    .toggle span {
      width: 20px;
      height: 20px;
      border-radius: 50%;
      background: #fff;
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
      transition: transform 0.15s;
    }
    .toggle.on {
      background: var(--kps-accent);
    }
    .toggle.on span {
      transform: translateX(18px);
    }
    .tile {
      width: 40px;
      height: 40px;
      border-radius: 11px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--kps-tile);
      background: color-mix(in srgb, var(--kps-tile) 15%, transparent);
    }
    .tile.light {
      --kps-tile: var(--kps-amber);
    }
    .tile.switch {
      --kps-tile: var(--kps-accent);
    }
    .tile.sensor {
      --kps-tile: var(--kps-success);
    }
    .tile.cover {
      --kps-tile: var(--kps-purple);
    }
    .tile.other {
      --kps-tile: var(--kps-muted);
    }
    .main {
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .name {
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--kps-muted);
    }
    .name input {
      font: inherit;
      font-size: 15px;
      font-weight: 600;
      color: var(--kps-text);
      background: transparent;
      border: none;
      border-bottom: 1px dashed var(--kps-line);
      border-radius: 0;
      padding: 2px 0;
      flex: 1;
      min-width: 0;
    }
    .name input::placeholder {
      color: var(--kps-text);
      opacity: 1;
    }
    .name input:focus {
      outline: none;
      border-bottom: 1px solid var(--kps-accent);
    }
    .meta {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      color: var(--kps-muted);
    }
    .meta a {
      color: var(--kps-accent);
      text-decoration: none;
    }
    .type {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 6px;
    }
    .domain {
      font-size: 14px;
      font-weight: 500;
    }
    .hint {
      height: 28px;
      padding: 0 10px;
      font-size: 12px;
      font-weight: 600;
      border-radius: 8px;
      gap: 6px;
      color: color-mix(in srgb, var(--kps-amber) 65%, var(--kps-text));
      background: color-mix(in srgb, var(--kps-amber) 16%, transparent);
    }
    .status {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 4px;
      text-align: right;
      min-width: 0;
    }
    .pill {
      --kps-tone: var(--kps-muted);
      font-size: 12px;
      font-weight: 600;
      padding: 4px 10px;
      border-radius: 999px;
      white-space: nowrap;
      color: color-mix(in srgb, var(--kps-tone) 75%, var(--kps-text));
      background: color-mix(in srgb, var(--kps-tone) 16%, transparent);
    }
    .pill.unchanged,
    .pill.kept {
      --kps-tone: var(--kps-success);
    }
    .pill.new,
    .pill.adopt {
      --kps-tone: var(--kps-accent);
    }
    .pill.pending {
      background: var(--kps-accent);
      color: var(--kps-on-accent);
    }
    .pill.changed {
      --kps-tone: var(--kps-warning);
    }
    .pill.removed,
    .pill.invalid {
      --kps-tone: var(--kps-error);
    }
    .reason {
      font-size: 12px;
      color: var(--kps-muted);
      max-width: 100%;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    @media (hover: hover) {
      .row .mark {
        opacity: 0;
      }
      .row:hover .mark,
      .row:focus-within .mark {
        opacity: 1;
      }
    }
    .drawer {
      grid-column: 3 / -1;
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding: 12px 14px;
      border-radius: 12px;
      background: var(--kps-soft);
      font-size: 13px;
    }
    .conflict-box {
      flex-direction: row;
      flex-wrap: wrap;
      align-items: center;
    }
    .addr {
      display: grid;
      grid-template-columns: 170px 130px minmax(0, 1fr) auto;
      align-items: center;
      gap: 6px 12px;
    }
    .addr input {
      font-family: var(--ha-font-family-code, ui-monospace, monospace);
    }
    .addr input.invalid {
      border-color: var(--kps-error);
    }
    .addr-note {
      color: var(--kps-muted);
      font-size: 12px;
    }
    .drawer select {
      align-self: flex-start;
    }
    .error-text {
      color: var(--kps-error);
      font-size: 12px;
    }
    .empty {
      padding: 48px 16px;
      text-align: center;
      color: var(--kps-muted);
    }

    /* ---------- apply bar (inverted colours, also in dark themes) */
    .bar-wrap {
      position: sticky;
      bottom: 16px;
      z-index: 4;
      max-width: 1120px;
      margin: 0 auto 16px;
      padding: 0 24px;
    }
    .bar {
      --kps-bar-text: var(--kps-surface);
      background: var(--kps-text);
      color: var(--kps-bar-text);
      border-radius: 16px;
      box-shadow: 0 12px 32px rgba(16, 24, 40, 0.24);
    }
    .bar-main {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 12px 18px;
      padding: 12px 14px 12px 22px;
    }
    .counts {
      flex: 1 1 auto;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 6px 18px;
      font-size: 14px;
    }
    .count {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--kps-accent);
    }
    .dot.change {
      background: var(--kps-warning);
    }
    .dot.remove {
      background: var(--kps-error);
    }
    .dim {
      opacity: 0.7;
    }
    .bar button.link.light {
      color: inherit;
      opacity: 0.8;
      text-decoration: underline;
      font-size: 14px;
    }
    .bar-actions {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-left: auto;
    }
    .bar button.outline {
      color: inherit;
      border-color: color-mix(in srgb, var(--kps-bar-text) 30%, transparent);
      height: 44px;
    }
    .bar button.primary {
      height: 44px;
      padding: 0 20px;
    }
    .bar .error-text {
      color: inherit;
    }
    .changes {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
      max-height: 40vh;
      overflow: auto;
      padding: 16px 22px 0;
      font-size: 14px;
    }
    .changes ul {
      margin: 4px 0 0;
      padding-left: 18px;
    }

    /* ---------- phone */
    @media (max-width: 760px) {
      .btn-label,
      .long,
      .app-icon {
        display: none;
      }
      .short {
        display: inline;
      }
      .tool {
        width: 44px;
        height: 44px;
        padding: 0;
      }
      .app-title {
        font-size: 17px;
      }
      .toolbar {
        padding: 0 8px 0 4px;
        gap: 4px;
      }
      .content {
        padding: 16px 16px 16px;
        gap: 14px;
      }
      .project h2 {
        font-size: 22px;
      }
      .staged {
        flex-wrap: wrap;
      }
      .staged > .grow {
        flex-basis: calc(100% - 60px);
      }
      .stats {
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px;
      }
      .stat {
        padding: 12px 14px;
      }
      .stat-value strong {
        font-size: 22px;
      }
      .room-head {
        padding: 12px 14px;
      }
      .progress {
        width: 56px;
      }
      .row {
        grid-template-columns: 36px minmax(0, 1fr) auto 48px;
        grid-template-areas:
          "tile main main toggle"
          ". type status status";
        padding: 12px 14px;
        gap: 10px 12px;
      }
      .tile {
        grid-area: tile;
        width: 36px;
        height: 36px;
      }
      .main {
        grid-area: main;
      }
      .toggle {
        grid-area: toggle;
        justify-self: end;
      }
      .type {
        grid-area: type;
        flex-direction: row;
        flex-wrap: wrap;
        align-items: center;
      }
      .status {
        grid-area: status;
      }
      .drawer {
        grid-column: 1 / -1;
      }
      .addr {
        grid-template-columns: minmax(0, 1fr) auto;
      }
      .addr label {
        grid-column: 1 / -1;
      }
      .addr-note {
        grid-column: 1 / -1;
      }
      .bar-wrap {
        padding: 0 12px;
      }
      .bar-main {
        padding: 12px;
      }
      .counts {
        gap: 4px 12px;
        font-size: 13px;
      }
      .segmented button {
        padding: 0 10px;
      }
    }
  `;var g={menu:"M4 6h16M4 12h16M4 18h16",home:"M3 10.5 12 4l9 6.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z",refresh:"M3 12a9 9 0 0 1 15.5-6.2L21 8M21 3v5h-5M21 12a9 9 0 0 1-15.5 6.2L3 16M3 21v-5h5",upload:"M12 16V4M7 9l5-5 5 5M4 20h16",search:"M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14zM21 21l-4.35-4.35",file:"M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8zM14 3v5h5M12 18v-6M9 15l3 3 3-3",pencil:"M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z",close:"M6 6l12 12M18 6 6 18",light:"M9 18h6M10 22h4M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.3 1 2.1V17h6v-.2c0-.8.4-1.6 1-2.1A7 7 0 0 0 12 2z",switch:"M8 7h8a5 5 0 0 1 0 10H8A5 5 0 0 1 8 7zM8 9.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5z",sensor:"M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z",cover:"M4 3h16M5 3v14M19 3v14M5 7h14M5 11h14M5 15h14M12 17v4",binary:"M6 3h9v18H6zM15 5h3v16M12 12h.01",scene:"M12 3l2.6 5.6 6 .7-4.5 4.1 1.2 6L12 16.4 6.7 19.4l1.2-6L3.4 9.3l6-.7z",climate:"M12 3v18M5.6 6.6l12.8 10.8M18.4 6.6 5.6 17.4M3 12h18",weather:"M12 3v2M5.6 5.6 7 7M3 12h2M17 7l1.4-1.4M16 12a4 4 0 1 0-6.9 2.8M8 19h9a3 3 0 0 0 0-6 4.5 4.5 0 0 0-8.6 1.4A2.4 2.4 0 0 0 8 19z",clock:"M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 7v5l3 2",generic:"M4 4h16v16H4zM9 9h6v6H9z",text:"M4 7V5h16v2M9 19h6M12 5v14"},Be={light:g.light,switch:g.switch,sensor:g.sensor,binary_sensor:g.binary,cover:g.cover,scene:g.scene,climate:g.climate,weather:g.weather,time:g.clock,date:g.clock,datetime:g.clock,text:g.text},We=n=>n==="light"||n==="switch"||n==="cover"?n:n==="sensor"||n==="climate"||n==="weather"?"sensor":"other",f=(n,t=22)=>d`<svg width=${t} height=${t} viewBox="0 0 24 24" fill="none"
  stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d=${n}></path></svg>`;customElements.define("knx-project-sync-panel",P);
/*! Bundled license information:

@lit/reactive-element/css-tag.js:
  (**
   * @license
   * Copyright 2019 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/reactive-element.js:
lit-html/lit-html.js:
lit-element/lit-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/is-server.js:
  (**
   * @license
   * Copyright 2022 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)
*/
