/**
 * Customizações para Item
 */

frappe.ui.form.on("Item", {
    ncm: function(frm) {
        // Remove formatação do NCM
        let ncm = frm.doc.ncm;
        if (!ncm) return;
        
        ncm = ncm.replace(/\D/g, "");
        
        if (ncm.length !== 8) {
            frappe.show_alert({
                message: __("NCM deve ter 8 dígitos"),
                indicator: "orange"
            });
        }
        
        frm.set_value("ncm", ncm);
        
        // Preenche gênero
        if (ncm.length >= 2) {
            frm.set_value("genero", ncm.substring(0, 2));
        }
    },
    
    cest: function(frm) {
        // Remove formatação do CEST
        let cest = frm.doc.cest;
        if (!cest) return;
        
        cest = cest.replace(/\D/g, "");
        
        if (cest.length !== 7) {
            frappe.show_alert({
                message: __("CEST deve ter 7 dígitos"),
                indicator: "orange"
            });
        }
        
        frm.set_value("cest", cest);
    }
});
