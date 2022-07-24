define("ace/mode/matching_brace_outdent",["require","exports","module","ace/range"],function(e,t,n){"use strict";var r=e("../range").Range,i=function(){};(function(){this.checkOutdent=function(e,t){return/^\s+$/.test(e)?/^\s*\}/.test(t):!1},this.autoOutdent=function(e,t){var n=e.getLine(t),i=n.match(/^(\s*\})/);if(!i)return 0;var s=i[1].length,o=e.findMatchingBracket({row:t,column:s});if(!o||o.row==t)return 0;var u=this.$getIndent(e.getLine(o.row));e.replace(new r(t,0,t,s-1),u)},this.$getIndent=function(e){return e.match(/^\s*/)[0]}}).call(i.prototype),t.MatchingBraceOutdent=i}),define("ace/mode/armymarkdown_highlight_rules",["require","exports","module","ace/lib/oop","ace/mode/text_highlight_rules"],function(e,t,n){"use strict";var r=e("../lib/oop"),i=e("./text_highlight_rules").TextHighlightRules,s=function(){this.$rules={start:[{token:"comment",regex:"#.*$"},{token:"keyword",regex:"[A-Z_]+[ ]*="}]}};r.inherits(s,i),t.MyNewHighlightRules=s}),define("ace/mode/folding/markdown",["require","exports","module","ace/lib/oop","ace/mode/folding/fold_mode","ace/range"],function(e,t,n){"use strict";var r=e("../../lib/oop"),i=e("./fold_mode").FoldMode,s=e("../../range").Range,o=t.FoldMode=function(){};r.inherits(o,i),function(){this.foldingStartMarker=/^(?:[=-]+\s*$|#{1,6} |`{3})/,this.getFoldWidget=function(e,t,n){var r=e.getLine(n);return this.foldingStartMarker.test(r)?r[0]=="`"?e.bgTokenizer.getState(n)=="start"?"end":"start":"start":""},this.getFoldWidgetRange=function(e,t,n){function l(t){return f=e.getTokens(t)[0],f&&f.type.lastIndexOf(c,0)===0}function h(){var e=f.value[0];return e=="="?6:e=="-"?5:7-f.value.search(/[^#]|$/)}var r=e.getLine(n),i=r.length,o=e.getLength(),u=n,a=n;if(!r.match(this.foldingStartMarker))return;if(r[0]=="`"){if(e.bgTokenizer.getState(n)!=="start"){while(++n<o){r=e.getLine(n);if(r[0]=="`"&r.substring(0,3)=="```")break}return new s(u,i,n,0)}while(n-->0){r=e.getLine(n);if(r[0]=="`"&r.substring(0,3)=="```")break}return new s(n,r.length,u,0)}var f,c="markup.heading";if(l(n)){var p=h();while(++n<o){if(!l(n))continue;var d=h();if(d>=p)break}a=n-(!f||["=","-"].indexOf(f.value[0])==-1?1:2);if(a>u)while(a>u&&/^\s*$/.test(e.getLine(a)))a--;if(a>u){var v=e.getLine(a).length;return new s(u,i,a,v)}}}}.call(o.prototype)}),define("ace/mode/armymarkdown",["require","exports","module","ace/lib/oop","ace/mode/text","ace/tokenizer","ace/mode/matching_brace_outdent","ace/mode/armymarkdown_highlight_rules","ace/mode/folding/markdown"],function(e,t,n){"use strict";var r=e("../lib/oop"),i=e("./text").Mode,s=e("../tokenizer").Tokenizer,o=e("./matching_brace_outdent").MatchingBraceOutdent,u=e("./armymarkdown_highlight_rules").MyNewHighlightRules,a=e("./folding/markdown").FoldMode,f=function(){this.HighlightRules=u,this.$outdent=new o};r.inherits(f,i),function(){this.lineCommentStart="#",this.blockComment={start:"/*",end:"*/"},this.getNextLineIndent=function(e,t,n){var r=this.$getIndent(t);return r},this.checkOutdent=function(e,t,n){return this.$outdent.checkOutdent(t,n)},this.autoOutdent=function(e,t,n){this.$outdent.autoOutdent(t,n)}}.call(f.prototype),t.Mode=f});                (function() {
                    window.require(["ace/mode/armymarkdown"], function(m) {
                        if (typeof module == "object" && typeof exports == "object" && module) {
                            module.exports = m;
                        }
                    });
                })();
            