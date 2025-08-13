export const htmlEscape = (s="") => s.replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");
export const md = (s="") => (window.marked?.parse ? window.marked.parse(s) : htmlEscape(s).replaceAll("\n","<br>"));
