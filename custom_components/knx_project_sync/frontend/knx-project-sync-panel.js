var M=globalThis,H=M.ShadowRoot&&(M.ShadyCSS===void 0||M.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,I=Symbol(),se=new WeakMap,k=class{constructor(t,e,s){if(this._$cssResult$=!0,s!==I)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o,e=this.t;if(H&&t===void 0){let s=e!==void 0&&e.length===1;s&&(t=se.get(e)),t===void 0&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),s&&se.set(e,t))}return t}toString(){return this.cssText}},ie=n=>new k(typeof n=="string"?n:n+"",void 0,I),D=(n,...t)=>{let e=n.length===1?n[0]:t.reduce((s,i,r)=>s+(a=>{if(a._$cssResult$===!0)return a.cssText;if(typeof a=="number")return a;throw Error("Value passed to 'css' function must be a 'css' function result: "+a+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+n[r+1],n[0]);return new k(e,n,I)},ne=(n,t)=>{if(H)n.adoptedStyleSheets=t.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(let e of t){let s=document.createElement("style"),i=M.litNonce;i!==void 0&&s.setAttribute("nonce",i),s.textContent=e.cssText,n.appendChild(s)}},W=H?n=>n:n=>n instanceof CSSStyleSheet?(t=>{let e="";for(let s of t.cssRules)e+=s.cssText;return ie(e)})(n):n;var{is:xe,defineProperty:we,getOwnPropertyDescriptor:Ae,getOwnPropertyNames:ke,getOwnPropertySymbols:Se,getPrototypeOf:Ee}=Object,U=globalThis,re=U.trustedTypes,Ce=re?re.emptyScript:"",Re=U.reactiveElementPolyfillSupport,S=(n,t)=>n,K={toAttribute(n,t){switch(t){case Boolean:n=n?Ce:null;break;case Object:case Array:n=n==null?n:JSON.stringify(n)}return n},fromAttribute(n,t){let e=n;switch(t){case Boolean:e=n!==null;break;case Number:e=n===null?null:Number(n);break;case Object:case Array:try{e=JSON.parse(n)}catch{e=null}}return e}},oe=(n,t)=>!xe(n,t),ae={attribute:!0,type:String,converter:K,reflect:!1,useDefault:!1,hasChanged:oe};Symbol.metadata??=Symbol("metadata"),U.litPropertyMetadata??=new WeakMap;var m=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=ae){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){let s=Symbol(),i=this.getPropertyDescriptor(t,s,e);i!==void 0&&we(this.prototype,t,i)}}static getPropertyDescriptor(t,e,s){let{get:i,set:r}=Ae(this.prototype,t)??{get(){return this[e]},set(a){this[e]=a}};return{get:i,set(a){let l=i?.call(this);r?.call(this,a),this.requestUpdate(t,l,s)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??ae}static _$Ei(){if(this.hasOwnProperty(S("elementProperties")))return;let t=Ee(this);t.finalize(),t.l!==void 0&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(S("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(S("properties"))){let e=this.properties,s=[...ke(e),...Se(e)];for(let i of s)this.createProperty(i,e[i])}let t=this[Symbol.metadata];if(t!==null){let e=litPropertyMetadata.get(t);if(e!==void 0)for(let[s,i]of e)this.elementProperties.set(s,i)}this._$Eh=new Map;for(let[e,s]of this.elementProperties){let i=this._$Eu(e,s);i!==void 0&&this._$Eh.set(i,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){let e=[];if(Array.isArray(t)){let s=new Set(t.flat(1/0).reverse());for(let i of s)e.unshift(W(i))}else t!==void 0&&e.push(W(t));return e}static _$Eu(t,e){let s=e.attribute;return s===!1?void 0:typeof s=="string"?s:typeof t=="string"?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),this.renderRoot!==void 0&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){let t=new Map,e=this.constructor.elementProperties;for(let s of e.keys())this.hasOwnProperty(s)&&(t.set(s,this[s]),delete this[s]);t.size>0&&(this._$Ep=t)}createRenderRoot(){let t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return ne(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,s){this._$AK(t,s)}_$ET(t,e){let s=this.constructor.elementProperties.get(t),i=this.constructor._$Eu(t,s);if(i!==void 0&&s.reflect===!0){let r=(s.converter?.toAttribute!==void 0?s.converter:K).toAttribute(e,s.type);this._$Em=t,r==null?this.removeAttribute(i):this.setAttribute(i,r),this._$Em=null}}_$AK(t,e){let s=this.constructor,i=s._$Eh.get(t);if(i!==void 0&&this._$Em!==i){let r=s.getPropertyOptions(i),a=typeof r.converter=="function"?{fromAttribute:r.converter}:r.converter?.fromAttribute!==void 0?r.converter:K;this._$Em=i;let l=a.fromAttribute(e,r.type);this[i]=l??this._$Ej?.get(i)??l,this._$Em=null}}requestUpdate(t,e,s,i=!1,r){if(t!==void 0){let a=this.constructor;if(i===!1&&(r=this[t]),s??=a.getPropertyOptions(t),!((s.hasChanged??oe)(r,e)||s.useDefault&&s.reflect&&r===this._$Ej?.get(t)&&!this.hasAttribute(a._$Eu(t,s))))return;this.C(t,e,s)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(t,e,{useDefault:s,reflect:i,wrapped:r},a){s&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,a??e??this[t]),r!==!0||a!==void 0)||(this._$AL.has(t)||(this.hasUpdated||s||(e=void 0),this._$AL.set(t,e)),i===!0&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}let t=this.scheduleUpdate();return t!=null&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[i,r]of this._$Ep)this[i]=r;this._$Ep=void 0}let s=this.constructor.elementProperties;if(s.size>0)for(let[i,r]of s){let{wrapped:a}=r,l=this[i];a!==!0||this._$AL.has(i)||l===void 0||this.C(i,void 0,r,l)}}let t=!1,e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(s=>s.hostUpdate?.()),this.update(e)):this._$EM()}catch(s){throw t=!1,this._$EM(),s}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(t){}firstUpdated(t){}};m.elementStyles=[],m.shadowRootOptions={mode:"open"},m[S("elementProperties")]=new Map,m[S("finalized")]=new Map,Re?.({ReactiveElement:m}),(U.reactiveElementVersions??=[]).push("2.1.2");var G=globalThis,le=n=>n,O=G.trustedTypes,de=O?O.createPolicy("lit-html",{createHTML:n=>n}):void 0,me="$lit$",_=`lit$${Math.random().toFixed(9).slice(2)}$`,fe="?"+_,Te=`<${fe}>`,$=document,C=()=>$.createComment(""),R=n=>n===null||typeof n!="object"&&typeof n!="function",J=Array.isArray,Pe=n=>J(n)||typeof n?.[Symbol.iterator]=="function",F=`[ 	
\f\r]`,E=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,ce=/-->/g,pe=/>/g,b=RegExp(`>|${F}(?:([^\\s"'>=/]+)(${F}*=${F}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),he=/'/g,ue=/"/g,_e=/^(?:script|style|textarea|title)$/i,Z=n=>(t,...e)=>({_$litType$:n,strings:t,values:e}),d=Z(1),Ke=Z(2),Fe=Z(3),x=Symbol.for("lit-noChange"),c=Symbol.for("lit-nothing"),ge=new WeakMap,y=$.createTreeWalker($,129);function ve(n,t){if(!J(n)||!n.hasOwnProperty("raw"))throw Error("invalid template strings array");return de!==void 0?de.createHTML(t):t}var Ne=(n,t)=>{let e=n.length-1,s=[],i,r=t===2?"<svg>":t===3?"<math>":"",a=E;for(let l=0;l<e;l++){let o=n[l],p,u,h=-1,g=0;for(;g<o.length&&(a.lastIndex=g,u=a.exec(o),u!==null);)g=a.lastIndex,a===E?u[1]==="!--"?a=ce:u[1]!==void 0?a=pe:u[2]!==void 0?(_e.test(u[2])&&(i=RegExp("</"+u[2],"g")),a=b):u[3]!==void 0&&(a=b):a===b?u[0]===">"?(a=i??E,h=-1):u[1]===void 0?h=-2:(h=a.lastIndex-u[2].length,p=u[1],a=u[3]===void 0?b:u[3]==='"'?ue:he):a===ue||a===he?a=b:a===ce||a===pe?a=E:(a=b,i=void 0);let f=a===b&&n[l+1].startsWith("/>")?" ":"";r+=a===E?o+Te:h>=0?(s.push(p),o.slice(0,h)+me+o.slice(h)+_+f):o+_+(h===-2?l:f)}return[ve(n,r+(n[e]||"<?>")+(t===2?"</svg>":t===3?"</math>":"")),s]},T=class n{constructor({strings:t,_$litType$:e},s){let i;this.parts=[];let r=0,a=0,l=t.length-1,o=this.parts,[p,u]=Ne(t,e);if(this.el=n.createElement(p,s),y.currentNode=this.el.content,e===2||e===3){let h=this.el.content.firstChild;h.replaceWith(...h.childNodes)}for(;(i=y.nextNode())!==null&&o.length<l;){if(i.nodeType===1){if(i.hasAttributes())for(let h of i.getAttributeNames())if(h.endsWith(me)){let g=u[a++],f=i.getAttribute(h).split(_),L=/([.?@])?(.*)/.exec(g);o.push({type:1,index:r,name:L[2],strings:f,ctor:L[1]==="."?Y:L[1]==="?"?q:L[1]==="@"?V:A}),i.removeAttribute(h)}else h.startsWith(_)&&(o.push({type:6,index:r}),i.removeAttribute(h));if(_e.test(i.tagName)){let h=i.textContent.split(_),g=h.length-1;if(g>0){i.textContent=O?O.emptyScript:"";for(let f=0;f<g;f++)i.append(h[f],C()),y.nextNode(),o.push({type:2,index:++r});i.append(h[g],C())}}}else if(i.nodeType===8)if(i.data===fe)o.push({type:2,index:r});else{let h=-1;for(;(h=i.data.indexOf(_,h+1))!==-1;)o.push({type:7,index:r}),h+=_.length-1}r++}}static createElement(t,e){let s=$.createElement("template");return s.innerHTML=t,s}};function w(n,t,e=n,s){if(t===x)return t;let i=s!==void 0?e._$Co?.[s]:e._$Cl,r=R(t)?void 0:t._$litDirective$;return i?.constructor!==r&&(i?._$AO?.(!1),r===void 0?i=void 0:(i=new r(n),i._$AT(n,e,s)),s!==void 0?(e._$Co??=[])[s]=i:e._$Cl=i),i!==void 0&&(t=w(n,i._$AS(n,t.values),i,s)),t}var B=class{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){let{el:{content:e},parts:s}=this._$AD,i=(t?.creationScope??$).importNode(e,!0);y.currentNode=i;let r=y.nextNode(),a=0,l=0,o=s[0];for(;o!==void 0;){if(a===o.index){let p;o.type===2?p=new P(r,r.nextSibling,this,t):o.type===1?p=new o.ctor(r,o.name,o.strings,this,t):o.type===6&&(p=new X(r,this,t)),this._$AV.push(p),o=s[++l]}a!==o?.index&&(r=y.nextNode(),a++)}return y.currentNode=$,i}p(t){let e=0;for(let s of this._$AV)s!==void 0&&(s.strings!==void 0?(s._$AI(t,s,e),e+=s.strings.length-2):s._$AI(t[e])),e++}},P=class n{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,s,i){this.type=2,this._$AH=c,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=s,this.options=i,this._$Cv=i?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode,e=this._$AM;return e!==void 0&&t?.nodeType===11&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=w(this,t,e),R(t)?t===c||t==null||t===""?(this._$AH!==c&&this._$AR(),this._$AH=c):t!==this._$AH&&t!==x&&this._(t):t._$litType$!==void 0?this.$(t):t.nodeType!==void 0?this.T(t):Pe(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==c&&R(this._$AH)?this._$AA.nextSibling.data=t:this.T($.createTextNode(t)),this._$AH=t}$(t){let{values:e,_$litType$:s}=t,i=typeof s=="number"?this._$AC(t):(s.el===void 0&&(s.el=T.createElement(ve(s.h,s.h[0]),this.options)),s);if(this._$AH?._$AD===i)this._$AH.p(e);else{let r=new B(i,this),a=r.u(this.options);r.p(e),this.T(a),this._$AH=r}}_$AC(t){let e=ge.get(t.strings);return e===void 0&&ge.set(t.strings,e=new T(t)),e}k(t){J(this._$AH)||(this._$AH=[],this._$AR());let e=this._$AH,s,i=0;for(let r of t)i===e.length?e.push(s=new n(this.O(C()),this.O(C()),this,this.options)):s=e[i],s._$AI(r),i++;i<e.length&&(this._$AR(s&&s._$AB.nextSibling,i),e.length=i)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){let s=le(t).nextSibling;le(t).remove(),t=s}}setConnected(t){this._$AM===void 0&&(this._$Cv=t,this._$AP?.(t))}},A=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,s,i,r){this.type=1,this._$AH=c,this._$AN=void 0,this.element=t,this.name=e,this._$AM=i,this.options=r,s.length>2||s[0]!==""||s[1]!==""?(this._$AH=Array(s.length-1).fill(new String),this.strings=s):this._$AH=c}_$AI(t,e=this,s,i){let r=this.strings,a=!1;if(r===void 0)t=w(this,t,e,0),a=!R(t)||t!==this._$AH&&t!==x,a&&(this._$AH=t);else{let l=t,o,p;for(t=r[0],o=0;o<r.length-1;o++)p=w(this,l[s+o],e,o),p===x&&(p=this._$AH[o]),a||=!R(p)||p!==this._$AH[o],p===c?t=c:t!==c&&(t+=(p??"")+r[o+1]),this._$AH[o]=p}a&&!i&&this.j(t)}j(t){t===c?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}},Y=class extends A{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===c?void 0:t}},q=class extends A{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==c)}},V=class extends A{constructor(t,e,s,i,r){super(t,e,s,i,r),this.type=5}_$AI(t,e=this){if((t=w(this,t,e,0)??c)===x)return;let s=this._$AH,i=t===c&&s!==c||t.capture!==s.capture||t.once!==s.once||t.passive!==s.passive,r=t!==c&&(s===c||i);i&&this.element.removeEventListener(this.name,this,s),r&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}},X=class{constructor(t,e,s){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=s}get _$AU(){return this._$AM._$AU}_$AI(t){w(this,t)}};var je=G.litHtmlPolyfillSupport;je?.(T,P),(G.litHtmlVersions??=[]).push("3.3.3");var be=(n,t,e)=>{let s=e?.renderBefore??t,i=s._$litPart$;if(i===void 0){let r=e?.renderBefore??null;s._$litPart$=i=new P(t.insertBefore(C(),r),r,void 0,e??{})}return i._$AI(n),i};var Q=globalThis,v=class extends m{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){let e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=be(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return x}};v._$litElement$=!0,v.finalized=!0,Q.litElementHydrateSupport?.({LitElement:v});var Le=Q.litElementPolyfillSupport;Le?.({LitElement:v});(Q.litElementVersions??=[]).push("4.2.2");var Me={menu:"Men\xFC",loading:"Lade \u2026",noProject:"Noch kein Projekt importiert. Lade eine .knxproj-Datei hoch oder lies das Projekt aus dem KNX-Panel ein.",lastImport:n=>`Letzter Import: ${n}`,neverImported:"Noch nicht importiert",count:n=>`${n} Entities angelegt`,fromKnx:"Aus KNX-Panel einlesen",upload:"Projektdatei hochladen",staged:"Neue Projektversion geladen. Pr\xFCfe die \xC4nderungen und \xFCbernimm sie, oder verwirf sie.",discardProject:"Projektversion verwerfen",loaded:"Projekt eingelesen. Neue Entities sind unter \u201ENeu verf\xFCgbar\u201C zu finden.",passwordNeeded:"Das Projekt ist passwortgesch\xFCtzt.",password:"Projekt-Passwort",open:"\xD6ffnen",cancel:"Abbrechen",search:"Suchen nach Name, Adresse, Raum \u2026",groupBy:"Gruppieren",byRoom:"Nach Raum",byType:"Nach Typ",noRoom:"Ohne Raum",nothingFound:"Keine Entities f\xFCr diesen Filter.",selectGroup:n=>`Alle in ${n} ausw\xE4hlen`,create:n=>`${n} anlegen`,name:"Name",type:"Typ",suggestLight:"\u{1F4A1} Als Licht?",suggestLightTitle:"Der Name deutet auf eine Lampe hin. Als Licht anlegen.",unmappedHint:"F\xFCr diese Gruppenadressen wurde kein Entity-Typ erkannt. Sie werden nicht angelegt. Lege sie bei Bedarf von Hand in der KNX-YAML oder im KNX-Panel an.",willAdd:"Wird hinzugef\xFCgt",willChange:"Wird ge\xE4ndert",willRemove:"Wird entfernt",summary:(n,t,e)=>`+${n} hinzuf\xFCgen \xB7 ${t} \xE4ndern \xB7 \u2212${e} entfernen`,stillPending:n=>`${n} neu verf\xFCgbar, nicht ausgew\xE4hlt`,discard:"Verwerfen",apply:"\xDCbernehmen",applying:"\xDCbernehme \u2026",applied:n=>`\xDCbernommen: ${n.new??0} neu, ${n.changed??0} ge\xE4ndert, ${n.deleted??0} entfernt. KNX wurde neu geladen.`,willAdopt:"Wird aus deiner YAML \xFCbernommen",adoptCount:n=>`${n} \xFCbernehmen`,adopt:"In App \xFCbernehmen",undo:"R\xFCckg\xE4ngig",ownYaml:"deiner eigenen KNX-YAML",conflictInfo:(n,t,e)=>`Schon in deiner YAML: ${n} \u201E${t}\u201C (${e}). Wird nicht doppelt angelegt.`,adoptInfo:n=>`Wird mit deiner Konfiguration in die App \xFCbernommen und aus ${n} entfernt. Vorher wird eine Sicherung angelegt.`,notAdoptable:"Nicht automatisch \xFCbernehmbar, bitte in der YAML entfernen.",markExisting:"Schon vorhanden",existingTitle:"Diese Entity gibt es schon (z. B. in deiner YAML als anderer Typ). Nicht anlegen.",resetConfig:"Auf Projekt zur\xFCcksetzen",ownConfigTitle:"Nutzt deine \xFCbernommene Konfiguration. Zur\xFCcksetzen auf die Erkennung aus dem ETS-Projekt.",adoptFailed:n=>`\xDCbernahme aus deiner YAML nicht m\xF6glich: ${n}. Es wurde nichts ge\xE4ndert.`,adoptReasons:{not_a_list_item:"der Eintrag ist kein einfacher Listeneintrag (\u201E- name: \u2026\u201C)",flow_style:"der Eintrag steht in Kurzschreibweise ({ \u2026 })",outside_config:"die Datei liegt au\xDFerhalb des Konfigurationsordners",line_not_found:"die Datei hat sich ge\xE4ndert, bitte neu laden",verification:"nach dem Entfernen h\xE4tte sich mehr als dieser Eintrag ge\xE4ndert"},filters:{all:"Alle",active:"Angelegt",pending:"Neu verf\xFCgbar",off:"Abgew\xE4hlt",existing:"Schon vorhanden",issues:"Nicht m\xF6glich",gone:"Nicht mehr im Projekt",unmapped:"Ohne Typ"},status:{new:"Wird hinzugef\xFCgt",changed:"Wird ge\xE4ndert",retyped:"Typ wird ge\xE4ndert",unchanged:"Aktiv",kept:"Behalten",removed:"Wird entfernt",pending:"Neu verf\xFCgbar",deselected:"Abgew\xE4hlt",deselected_removed:"Wird entfernt",excluded:"Typ ausgeschlossen",duplicate:"Doppelt",invalid:"Ung\xFCltig",conflict:"Eigene YAML",existing:"Schon vorhanden",adopt:"Wird \xFCbernommen",own_config:"Aktiv \xB7 eigene Konfiguration"},reasons:{own_yaml:"Schon in deiner eigenen KNX-YAML definiert",light:"GA schon von einem Licht belegt",unique_id:"Gleiche Gruppenadresse wie eine andere Entity"},domains:{switch:"Schalter",light:"Licht",binary_sensor:"Bin\xE4rsensor",sensor:"Sensor",time:"Uhrzeit",date:"Datum",datetime:"Datum/Uhrzeit",cover:"Rollladen/Jalousie",scene:"Szene",climate:"Klima",weather:"Wetter"},errors:{invalid_password:"Falsches oder fehlendes Projekt-Passwort.",invalid_project:"Keine lesbare ETS-Projektdatei.",no_knx_project:"Im KNX-Panel ist kein Projekt hochgeladen.",not_set_up:"KNX Project Sync ist nicht eingerichtet.",no_project:"Es wurde noch kein Projekt importiert."}},He={menu:"Menu",loading:"Loading \u2026",noProject:"No project imported yet. Upload a .knxproj file or read the project from the KNX panel.",lastImport:n=>`Last import: ${n}`,neverImported:"Not imported yet",count:n=>`${n} entities created`,fromKnx:"Read from KNX panel",upload:"Upload project file",staged:"New project version loaded. Review the changes and apply them, or discard them.",discardProject:"Discard project version",loaded:"Project loaded. New entities are listed under \u201CNewly available\u201D.",passwordNeeded:"The project is password protected.",password:"Project password",open:"Open",cancel:"Cancel",search:"Search name, address, room \u2026",groupBy:"Group by",byRoom:"By room",byType:"By type",noRoom:"No room",nothingFound:"No entities for this filter.",selectGroup:n=>`Select all in ${n}`,create:n=>`Create ${n}`,name:"Name",type:"Type",suggestLight:"\u{1F4A1} A light?",suggestLightTitle:"The name suggests a lamp. Create it as a light.",unmappedHint:"No entity type was detected for these group addresses, so they are not created. Add them by hand in the KNX YAML or the KNX panel if needed.",willAdd:"Will be added",willChange:"Will be changed",willRemove:"Will be removed",summary:(n,t,e)=>`+${n} add \xB7 ${t} change \xB7 \u2212${e} remove`,stillPending:n=>`${n} newly available, not selected`,discard:"Discard",apply:"Apply",applying:"Applying \u2026",applied:n=>`Applied: ${n.new??0} new, ${n.changed??0} changed, ${n.deleted??0} removed. KNX was reloaded.`,willAdopt:"Taken over from your YAML",adoptCount:n=>`${n} take over`,adopt:"Take over into the app",undo:"Undo",ownYaml:"your own KNX YAML",conflictInfo:(n,t,e)=>`Already in your YAML: ${n} \u201C${t}\u201D (${e}). Not created twice.`,adoptInfo:n=>`Taken over into the app with your configuration and removed from ${n}. A backup is made first.`,notAdoptable:"Cannot be taken over automatically, please remove it from the YAML.",markExisting:"Already exists",existingTitle:"This entity already exists (e.g. in your YAML as another type). Do not create it.",resetConfig:"Reset to project",ownConfigTitle:"Uses your taken-over configuration. Reset to what the ETS project detects.",adoptFailed:n=>`Could not take over from your YAML: ${n}. Nothing was changed.`,adoptReasons:{not_a_list_item:"the entry is not a plain list item (\u201C- name: \u2026\u201D)",flow_style:"the entry uses the short flow style ({ \u2026 })",outside_config:"the file is outside the configuration folder",line_not_found:"the file has changed, please reload",verification:"removing it would have changed more than this entry"},filters:{all:"All",active:"Created",pending:"Newly available",off:"Deselected",existing:"Already exists",issues:"Not possible",gone:"No longer in project",unmapped:"No type"},status:{new:"Will be added",changed:"Will change",retyped:"Type changes",unchanged:"Active",kept:"Kept",removed:"Will be removed",pending:"Newly available",deselected:"Deselected",deselected_removed:"Will be removed",excluded:"Type excluded",duplicate:"Duplicate",invalid:"Invalid",conflict:"Own YAML",existing:"Already exists",adopt:"Will be taken over",own_config:"Active \xB7 own configuration"},reasons:{own_yaml:"Already defined in your own KNX YAML",light:"GA already used by a light",unique_id:"Same group address as another entity"},domains:{switch:"Switch",light:"Light",binary_sensor:"Binary sensor",sensor:"Sensor",time:"Time",date:"Date",datetime:"Date/time",cover:"Cover",scene:"Scene",climate:"Climate",weather:"Weather"},errors:{invalid_password:"Wrong or missing project password.",invalid_project:"Not a readable ETS project file.",no_knx_project:"No project is uploaded in the KNX panel.",not_set_up:"KNX Project Sync is not set up.",no_project:"No project has been imported yet."}},ee={de:Me,en:He};var te=new Set(["new","changed","unchanged","kept"]),N=new Set(["excluded","duplicate","invalid","conflict","removed","existing"]),Ue=["all","active","pending","off","existing","issues","gone","unmapped"],ye=(n,t)=>{switch(t){case"all":return!0;case"active":return te.has(n.status);case"pending":return n.status==="pending";case"existing":return n.status==="existing";case"off":return n.status==="deselected";case"issues":return["excluded","duplicate","invalid","conflict"].includes(n.status);case"gone":return!n.in_project;default:return!1}},z=n=>{let t={};for(let[e,s]of Object.entries(n)){let i={};(s.enabled===!0||s.enabled===!1)&&(i.enabled=s.enabled),s.domain&&(i.domain=s.domain),s.name&&s.name.trim()&&(i.name=s.name.trim()),s.existing&&(i.existing=!0),s.adopt&&(i.adopt=!0),s.config&&(i.config=s.config),Object.keys(i).length&&(t[e]=i)}return t},Oe=(n,t)=>JSON.stringify($e(z(n)))===JSON.stringify($e(z(t))),$e=n=>Object.fromEntries(Object.entries(n).sort(([t],[e])=>t.localeCompare(e))),j=class extends v{constructor(){super(...arguments);this.narrow=!1;this._data=null;this._draft={};this._search="";this._filter="all";this._group="room";this._busy=null;this._error=null;this._message=null;this._passwordFor=null;this._showChanges=!1;this._loaded=!1;this._request=0}get t(){let e=(this.hass?.locale?.language||this.hass?.language||"en").slice(0,2);return ee[e]??ee.en}updated(e){if(e.has("hass")&&this.hass&&!this._loaded){this._loaded=!0,this._refresh(void 0,!0);try{let s=JSON.parse(localStorage.getItem("knx-project-sync-view")??"{}");(s.group==="room"||s.group==="domain")&&(this._group=s.group)}catch{}}}async _refresh(e,s=!1){let i=++this._request;try{let r={type:"knx_project_sync/plan"};e&&(r.selection=z(e));let a=await this.hass.callWS(r);if(i!==this._request)return;this._data=a,s&&(this._draft=structuredClone(a.stored_selection??{})),this._error=null}catch(r){i===this._request&&(this._error=this._errorText(r))}}_scheduleRefresh(){window.clearTimeout(this._timer),this._timer=window.setTimeout(()=>this._refresh(this._draft),250)}_errorText(e){let s=e;return s.code==="adopt_failed"?this.t.adoptFailed(this.t.adoptReasons[s.message??""]??s.message??""):s.code&&this.t.errors[s.code]||s.message||String(e)}async _loadKnxProject(){await this._run("load",async()=>{await this.hass.callWS({type:"knx_project_sync/load_project",source:"knx_project"}),await this._refresh(this._draft),this._message=this.t.loaded})}async _upload(e,s){await this._run("load",async()=>{let i=new FormData;i.append("file",e);let r=await this.hass.fetchWithAuth("/api/file_upload",{method:"POST",body:i});if(!r.ok)throw new Error(`${r.status} ${await r.text()}`);let{file_id:a}=await r.json();try{await this.hass.callWS({type:"knx_project_sync/load_project",source:"upload",file_id:a,...s?{password:s}:{}})}catch(l){throw l.code==="invalid_password"&&(this._passwordFor=e),l}this._passwordFor=null,await this._refresh(this._draft),this._message=this.t.loaded})}async _discard(){await this._run("discard",async()=>{this._data?.staged&&await this.hass.callWS({type:"knx_project_sync/discard"}),this._showChanges=!1,await this._refresh(void 0,!0)})}async _apply(){await this._run("apply",async()=>{let e=await this.hass.callWS({type:"knx_project_sync/apply",selection:z(this._draft)});this._showChanges=!1,await this._refresh(void 0,!0),this._message=this.t.applied(e)})}async _run(e,s){this._busy=e,this._error=null,this._message=null;try{await s()}catch(i){this._error=this._errorText(i)}finally{this._busy=null}}_choose(e,s){let i={...this._draft[e]??{},...s};this._draft={...this._draft,[e]:i},this._scheduleRefresh()}_checked(e){let s=this._draft[e.key]?.enabled;return s===!0||s===!1?s&&!N.has(e.status):te.has(e.status)}_toggleMany(e,s){let i={...this._draft};for(let r of e)N.has(r.status)||(i[r.key]={...i[r.key]??{},enabled:s});this._draft=i,this._scheduleRefresh()}get _dirty(){return this._data?this._data.staged||!Oe(this._draft,this._data.stored_selection??{})||!!this._data.has_changes:!1}_visible(){let e=this._search.trim().toLowerCase();return(this._data?.entities??[]).filter(s=>ye(s,this._filter)?e?[s.name,s.ets_name,s.room,s.key,s.entity_id,s.domain,...s.addresses.map(r=>r.address)].filter(Boolean).join(" ").toLowerCase().includes(e):!0:!1)}render(){let e=this.t,s=this._data;return d`
      <div class="toolbar">
        ${this.narrow?d`<button class="icon" title=${e.menu} @click=${this._toggleMenu}>
              <svg viewBox="0 0 24 24"><path d="M3,6H21V8H3V6M3,11H21V13H3V11M3,16H21V18H3V16Z" /></svg>
            </button>`:c}
        <div class="title">KNX Project Sync</div>
      </div>
      <div class="content">
        ${this._renderHeader()} ${this._error?d`<div class="alert error">${this._error}</div>`:c}
        ${this._message?d`<div class="alert info">${this._message}</div>`:c}
        ${this._passwordFor?this._renderPassword():c}
        ${s?s.project?d`${this._renderFilters()} ${this._filter==="unmapped"?this._renderUnmapped():this._renderGroups()}`:d`<div class="empty">${e.noProject}</div>`:d`<div class="empty">${e.loading}</div>`}
      </div>
      ${s?.project&&this._dirty?this._renderBar():c}
    `}_renderHeader(){let e=this.t,s=this._data,i=s?.last_import;return d`
      <div class="header">
        <div>
          <div class="project">${s?.project??"\u2013"}</div>
          <div class="sub">
            ${i?e.lastImport(new Date(i.time).toLocaleString(this.hass.language)):e.neverImported}
            ${s?d` · ${e.count(s.entities.filter(r=>te.has(r.status)).length)}`:c}
          </div>
        </div>
        <div class="actions">
          ${s?.has_knx_project?d`<button ?disabled=${!!this._busy} @click=${this._loadKnxProject}>${e.fromKnx}</button>`:c}
          <label class="button ${this._busy?"disabled":""}">
            ${e.upload}
            <input
              type="file"
              accept=".knxproj"
              hidden
              ?disabled=${!!this._busy}
              @change=${r=>{let a=r.target,l=a.files?.[0];a.value="",l&&this._upload(l)}}
            />
          </label>
        </div>
      </div>
      ${s?.staged?d`<div class="alert warn">
            <span>${e.staged}</span>
            <button class="text" @click=${this._discard}>${e.discardProject}</button>
          </div>`:c}
    `}_renderPassword(){let e=this.t;return d`<form class="alert warn" @submit=${i=>{i.preventDefault();let r=this.renderRoot.querySelector("#password");this._passwordFor&&r&&this._upload(this._passwordFor,r.value)}}>
      <span>${e.passwordNeeded}</span>
      <input id="password" type="password" autocomplete="off" placeholder=${e.password} />
      <button type="submit" ?disabled=${!!this._busy}>${e.open}</button>
      <button type="button" class="text" @click=${()=>this._passwordFor=null}>${e.cancel}</button>
    </form>`}_renderFilters(){let e=this.t,s=this._data?.entities??[],i=r=>r==="unmapped"?this._data?.unmapped.length??0:s.filter(a=>ye(a,r)).length;return d`
      <div class="filters">
        <input
          class="search"
          type="search"
          placeholder=${e.search}
          .value=${this._search}
          @input=${r=>this._search=r.target.value}
        />
        <select
          aria-label=${e.groupBy}
          .value=${this._group}
          @change=${r=>{this._group=r.target.value;try{localStorage.setItem("knx-project-sync-view",JSON.stringify({group:this._group}))}catch{}}}
        >
          <option value="room">${e.byRoom}</option>
          <option value="domain">${e.byType}</option>
        </select>
      </div>
      <div class="chips" role="tablist">
        ${Ue.map(r=>{let a=i(r);return a===0&&r!=="all"&&r!==this._filter?c:d`<button
            role="tab"
            class="chip ${r===this._filter?"active":""} ${r==="pending"?"accent":""}"
            aria-selected=${r===this._filter}
            @click=${()=>this._filter=r}
          >
            ${e.filters[r]} <span class="n">${a}</span>
          </button>`})}
      </div>
    `}_renderGroups(){let e=this.t,s=this._visible();if(!s.length)return d`<div class="empty">${e.nothingFound}</div>`;let i=new Map;for(let a of s){let l=this._group==="room"?a.room||e.noRoom:e.domains[a.domain]??a.domain;i.set(l,[...i.get(l)??[],a])}let r=[...i.entries()].sort(([a],[l])=>a===e.noRoom?1:l===e.noRoom?-1:a.localeCompare(l,this.hass.language));return d`${r.map(([a,l])=>{let o=l.filter(u=>!N.has(u.status)),p=o.filter(u=>this._checked(u)).length;return d`<section class="group">
        <div class="group-head">
          <input
            type="checkbox"
            aria-label=${e.selectGroup(a)}
            .checked=${o.length>0&&p===o.length}
            .indeterminate=${p>0&&p<o.length}
            ?disabled=${!o.length}
            @change=${u=>this._toggleMany(o,u.target.checked)}
          />
          <h2>${a}</h2>
          <span class="n">${p}/${l.length}</span>
        </div>
        <div class="rows">${l.map(u=>this._renderRow(u))}</div>
      </section>`})}`}_renderRow(e){let s=this.t,i=this._draft[e.key]??{},r=N.has(e.status),a=this._checked(e),l=i.domain||e.detected_domain;return d`<div class="row ${a?"":"off"} ${r?"blocked":""}">
      <input
        type="checkbox"
        class="check"
        aria-label=${s.create(e.ets_name??e.key)}
        .checked=${a}
        ?disabled=${r}
        @change=${o=>this._choose(e.key,{enabled:o.target.checked})}
      />
      <div class="main">
        <input
          class="name"
          type="text"
          .value=${i.name??""}
          placeholder=${e.ets_name??e.key}
          aria-label=${s.name}
          ?disabled=${!e.in_project}
          @change=${o=>this._choose(e.key,{name:o.target.value})}
        />
        <div class="meta">
          ${e.addresses.map(o=>d`<code title=${o.field}>${o.address}</code>`)}
          ${this._group==="domain"&&e.room?d`<span>${e.room}</span>`:c}
          ${e.entity_id?d`<a href="#" @click=${o=>this._moreInfo(o,e.entity_id)}>${e.entity_id}</a>`:c}
        </div>
      </div>
      <div class="type">
        ${e.domains.length>1?d`<select
              aria-label=${s.type}
              ?disabled=${r}
              .value=${l}
              @change=${o=>this._choose(e.key,{domain:o.target.value})}
            >
              ${e.domains.map(o=>d`<option value=${o} ?selected=${o===l}>${s.domains[o]??o}</option>`)}
            </select>`:d`<span class="domain">${s.domains[e.domain]??e.domain}</span>`}
        ${e.suggest_light&&l==="switch"&&!r?d`<button class="hint" title=${s.suggestLightTitle} @click=${()=>this._choose(e.key,{domain:"light"})}>
              ${s.suggestLight}
            </button>`:c}
      </div>
      <div class="status">
        <span class="badge ${e.adopt?"adopt":e.status}">${this._statusLabel(e)}</span>
        ${e.reason&&r&&!e.conflict_with?d`<div class="reason" title=${e.reason}>${this._reasonLabel(e)}</div>`:c}
        ${this._renderActions(e,i)}
      </div>
      ${e.conflict_with?this._renderConflict(e,i):c}
    </div>`}_renderConflict(e,s){let i=this.t,r=e.conflict_with,a=r.file?`${r.file}${r.line?`:${r.line}`:""}`:i.ownYaml;return d`<div class="conflict-box">
      <span>
        ${e.adopt?i.adoptInfo(a):i.conflictInfo(i.domains[r.domain]??r.domain,r.name??"",a)}
      </span>
      ${s.adopt?d`<button class="text" @click=${()=>this._choose(e.key,{adopt:null})}>${i.undo}</button>`:r.adoptable?d`<button @click=${()=>this._choose(e.key,{adopt:!0})}>${i.adopt}</button>`:d`<span class="sub">${i.notAdoptable}</span>`}
    </div>`}_renderActions(e,s){let i=this.t;return e.in_project?e.status==="existing"||s.existing?d`<button class="link" @click=${()=>this._choose(e.key,{existing:null})}>${i.undo}</button>`:e.own_config&&s.config?d`<button class="link" title=${i.ownConfigTitle} @click=${()=>this._choose(e.key,{config:null,domain:null})}>
        ${i.resetConfig}
      </button>`:e.status==="conflict"||N.has(e.status)||e.adopt?c:d`<button class="link mark" title=${i.existingTitle} @click=${()=>this._choose(e.key,{existing:!0})}>
      ${i.markExisting}
    </button>`:c}_statusLabel(e){let s=this.t;return e.adopt?s.status.adopt:e.own_config&&e.status==="unchanged"?s.status.own_config:e.status==="deselected"&&e.entity_id?s.status.deselected_removed:e.status==="changed"&&e.previous_domain&&e.previous_domain!==e.domain?s.status.retyped:s.status[e.status]??e.status}_reasonLabel(e){let s=this.t;return e.status==="conflict"?s.reasons.own_yaml:e.status==="duplicate"?e.reason==="light"?s.reasons.light:s.reasons.unique_id:e.reason??""}_renderUnmapped(){let e=this.t,s=this._search.trim().toLowerCase(),i=(this._data?.unmapped??[]).filter(r=>!s||`${r.address} ${r.name} ${r.dpt??""}`.toLowerCase().includes(s));return d`<p class="sub">${e.unmappedHint}</p>
      <div class="rows">
        ${i.map(r=>d`<div class="row off unmapped">
            <code>${r.address}</code>
            <div class="main">${r.name}</div>
            <span class="domain">${r.dpt?`DPT ${r.dpt}`:"\u2013"}</span>
          </div>`)}
      </div>`}_renderBar(){let e=this.t,s=this._data?.summary??{},i=this._data?.entities??[],r=i.filter(p=>p.status==="new"&&!p.adopt),a=i.filter(p=>p.adopt),l=i.filter(p=>p.status==="changed"),o=i.filter(p=>p.status==="removed"||(p.status==="deselected"||p.status==="existing")&&p.entity_id);return d`<div class="bar">
      ${this._showChanges?d`<div class="changes">
            ${[[e.willAdd,r],[e.willChange,l],[e.willRemove,o],[e.willAdopt,a]].map(([p,u])=>u.length?d`<div>
                    <strong>${p}</strong>
                    <ul>
                      ${u.map(h=>d`<li>${h.name??h.key} <span class="sub">(${e.domains[h.domain]??h.domain})</span></li>`)}
                    </ul>
                  </div>`:c)}
          </div>`:c}
      <div class="bar-main">
        <div class="bar-info">
          <button
            class="text summary"
            aria-expanded=${this._showChanges}
            @click=${()=>this._showChanges=!this._showChanges}
          >
            ${e.summary(r.length,l.length,o.length)}${a.length?` \xB7 ${e.adoptCount(a.length)}`:""} ${this._showChanges?"\u25BE":"\u25B4"}
          </button>
          ${s.pending?d`<span class="sub">${e.stillPending(s.pending)}</span>`:c}
        </div>
        <div class="bar-actions">
          <button class="text" ?disabled=${!!this._busy} @click=${this._discard}>${e.discard}</button>
          <button class="primary" ?disabled=${!!this._busy} @click=${this._apply}>
            ${this._busy==="apply"?e.applying:e.apply}
          </button>
        </div>
      </div>
    </div>`}_toggleMenu(){this.dispatchEvent(new CustomEvent("hass-toggle-menu",{bubbles:!0,composed:!0}))}_moreInfo(e,s){e.preventDefault(),this.dispatchEvent(new CustomEvent("hass-more-info",{detail:{entityId:s},bubbles:!0,composed:!0}))}};j.properties={hass:{attribute:!1},narrow:{type:Boolean},_data:{state:!0},_draft:{state:!0},_search:{state:!0},_filter:{state:!0},_group:{state:!0},_busy:{state:!0},_error:{state:!0},_message:{state:!0},_passwordFor:{state:!0},_showChanges:{state:!0}},j.styles=D`
    :host {
      display: block;
      min-height: 100vh;
      background: var(--primary-background-color, #fafafa);
      color: var(--primary-text-color, #212121);
      font-family: var(--ha-font-family-body, Roboto, system-ui, sans-serif);
      --radius: var(--ha-card-border-radius, 12px);
      --line: var(--divider-color, rgba(0, 0, 0, 0.12));
      --muted: var(--secondary-text-color, #727272);
      --surface: var(--card-background-color, #fff);
      --accent: var(--primary-color, #03a9f4);
    }
    .toolbar {
      display: flex;
      align-items: center;
      gap: 8px;
      height: var(--header-height, 56px);
      padding: 0 16px;
      background: var(--app-header-background-color, var(--primary-color, #03a9f4));
      color: var(--app-header-text-color, #fff);
      position: sticky;
      top: 0;
      z-index: 3;
    }
    .toolbar .title {
      font-size: 20px;
      font-weight: 400;
    }
    .icon {
      background: none;
      border: none;
      color: inherit;
      padding: 8px;
      margin-left: -8px;
      cursor: pointer;
    }
    .icon svg {
      width: 24px;
      height: 24px;
      fill: currentColor;
    }
    .content {
      max-width: 1100px;
      margin: 0 auto;
      padding: 16px 16px 24px;
    }
    .header {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      margin-bottom: 12px;
    }
    .project {
      font-size: 22px;
    }
    .sub {
      color: var(--muted);
      font-size: 13px;
    }
    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    button,
    .button {
      font: inherit;
      font-size: 14px;
      font-weight: 500;
      border-radius: 18px;
      padding: 7px 16px;
      border: 1px solid var(--line);
      background: var(--surface);
      color: var(--accent);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
    }
    button:disabled,
    .button.disabled {
      opacity: 0.5;
      cursor: default;
    }
    button.primary {
      background: var(--accent);
      color: var(--text-primary-color, #fff);
      border-color: var(--accent);
    }
    button.text {
      border-color: transparent;
      background: none;
    }
    .alert {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
      padding: 10px 14px;
      border-radius: var(--radius);
      margin-bottom: 12px;
      background: var(--surface);
      border-left: 4px solid var(--accent);
    }
    .alert.error {
      border-color: var(--error-color, #db4437);
    }
    .alert.warn {
      border-color: var(--warning-color, #ffa600);
    }
    .alert span {
      flex: 1 1 240px;
    }
    input[type="text"],
    input[type="search"],
    input[type="password"],
    select {
      font: inherit;
      font-size: 14px;
      color: var(--primary-text-color);
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 7px 10px;
      min-width: 0;
    }
    input:focus-visible,
    select:focus-visible,
    button:focus-visible {
      outline: 2px solid var(--accent);
      outline-offset: 1px;
    }
    .filters {
      display: flex;
      gap: 8px;
      margin-bottom: 8px;
    }
    .search {
      flex: 1;
    }
    .chips {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-bottom: 16px;
    }
    .chip {
      color: var(--primary-text-color);
      padding: 4px 12px;
      font-weight: 400;
    }
    .chip.active {
      background: var(--accent);
      border-color: var(--accent);
      color: var(--text-primary-color, #fff);
    }
    .chip.accent:not(.active) {
      border-color: var(--accent);
    }
    .chip .n {
      color: inherit;
      opacity: 0.7;
      margin-left: 4px;
    }
    .group {
      background: var(--surface);
      border-radius: var(--radius);
      box-shadow: var(--ha-card-box-shadow, none);
      border: 1px solid var(--ha-card-border-color, var(--line));
      margin-bottom: 16px;
      overflow: hidden;
    }
    .group-head {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 16px;
      border-bottom: 1px solid var(--line);
    }
    .group-head h2 {
      font-size: 16px;
      font-weight: 500;
      margin: 0;
      flex: 1;
    }
    .n {
      color: var(--muted);
      font-size: 13px;
    }
    .row {
      display: grid;
      grid-template-columns: auto minmax(0, 1fr) 150px 150px;
      gap: 12px;
      align-items: center;
      padding: 8px 16px;
      border-bottom: 1px solid var(--line);
    }
    .rows > .row:last-child {
      border-bottom: none;
    }
    .row.off .name,
    .row.off .meta {
      opacity: 0.6;
    }
    .row.unmapped {
      grid-template-columns: 80px minmax(0, 1fr) auto;
    }
    .check {
      width: 18px;
      height: 18px;
      accent-color: var(--accent);
    }
    .main {
      min-width: 0;
    }
    input.name {
      width: 100%;
      box-sizing: border-box;
      border-color: transparent;
      border-bottom: 1px dashed var(--line);
      border-radius: 4px 4px 0 0;
      background: transparent;
      padding: 4px 6px;
      margin-left: -6px;
    }
    input.name:hover,
    input.name:focus {
      border-color: var(--line);
      background: var(--surface);
    }
    input.name::placeholder {
      color: var(--primary-text-color);
      opacity: 1;
    }
    .meta {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      font-size: 12px;
      color: var(--muted);
      margin-top: 2px;
    }
    .meta a {
      color: var(--accent);
      text-decoration: none;
    }
    code {
      font-family: var(--ha-font-family-code, ui-monospace, monospace);
      font-size: 12px;
      background: var(--secondary-background-color, rgba(0, 0, 0, 0.05));
      border-radius: 4px;
      padding: 1px 5px;
    }
    .type {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 4px;
    }
    .type select {
      width: 100%;
    }
    .domain {
      font-size: 14px;
    }
    .hint {
      font-size: 12px;
      padding: 2px 10px;
      border-style: dashed;
    }
    .status {
      text-align: right;
      min-width: 0;
    }
    .badge {
      display: inline-block;
      font-size: 12px;
      border-radius: 10px;
      padding: 2px 10px;
      background: var(--secondary-background-color, rgba(0, 0, 0, 0.06));
      color: var(--primary-text-color);
      white-space: nowrap;
    }
    .badge.new,
    .badge.pending {
      background: var(--accent);
      color: var(--text-primary-color, #fff);
    }
    .badge.changed {
      background: var(--warning-color, #ffa600);
      color: #000;
    }
    .badge.unchanged {
      background: var(--success-color, #43a047);
      color: #fff;
    }
    .badge.removed,
    .badge.invalid {
      background: var(--error-color, #db4437);
      color: #fff;
    }
    .reason {
      font-size: 12px;
      color: var(--muted);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      margin-top: 2px;
    }
    .badge.adopt {
      background: var(--accent);
      color: var(--text-primary-color, #fff);
    }
    .badge.existing {
      background: var(--secondary-background-color, rgba(0, 0, 0, 0.06));
    }
    button.link {
      border: none;
      background: none;
      padding: 2px 0;
      margin-top: 4px;
      font-size: 12px;
      font-weight: 500;
      border-radius: 4px;
    }
    /* "already exists" only on hover/focus, it is rarely needed */
    @media (hover: hover) {
      .row .mark {
        opacity: 0;
      }
      .row:hover .mark,
      .row:focus-within .mark {
        opacity: 1;
      }
    }
    .conflict-box {
      grid-column: 2 / -1;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px 12px;
      font-size: 13px;
      padding: 8px 12px;
      border-radius: 8px;
      background: var(--secondary-background-color, rgba(0, 0, 0, 0.04));
    }
    .conflict-box span:first-child {
      flex: 1 1 260px;
    }
    .conflict-box button {
      padding: 4px 12px;
      font-size: 13px;
    }
    .empty {
      padding: 48px 16px;
      text-align: center;
      color: var(--muted);
    }
    .bar {
      position: sticky;
      bottom: 0;
      background: var(--surface);
      border-top: 1px solid var(--line);
      box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.12);
      z-index: 4;
    }
    .bar-main {
      max-width: 1100px;
      margin: 0 auto;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
      padding: 10px 16px;
    }
    .bar-info {
      flex: 1 1 auto;
      min-width: 0;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      column-gap: 12px;
    }
    .bar .summary {
      color: var(--primary-text-color);
      padding-left: 0;
    }
    .bar-actions {
      display: flex;
      gap: 8px;
      margin-left: auto;
    }
    .changes {
      max-width: 1100px;
      margin: 0 auto;
      max-height: 40vh;
      overflow: auto;
      padding: 12px 16px 0;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
      font-size: 14px;
    }
    .changes ul {
      margin: 4px 0 0;
      padding-left: 18px;
    }
    @media (max-width: 700px) {
      .row {
        grid-template-columns: auto minmax(0, 1fr) auto;
        grid-template-areas: "check main main" ". type status";
        row-gap: 6px;
      }
      .check {
        grid-area: check;
      }
      .main {
        grid-area: main;
      }
      .type {
        grid-area: type;
        flex-direction: row;
        align-items: center;
      }
      .type select {
        width: auto;
      }
      .status {
        grid-area: status;
      }
      .conflict-box {
        grid-column: 1 / -1;
      }
    }
  `;customElements.define("knx-project-sync-panel",j);
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
