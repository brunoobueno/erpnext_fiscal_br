/**
 * Customizações para Customer
 */

frappe.ui.form.on("Customer", {
    cpf_cnpj: function(frm) {
        // Formata CPF/CNPJ
        let doc = frm.doc.cpf_cnpj;
        if (!doc) return;
        
        // Remove formatação
        doc = doc.replace(/\D/g, "");
        
        // Valida e formata
        if (doc.length === 11) {
            // CPF
            frm.set_value("cpf_cnpj", erpnext_fiscal_br.formatar_cpf(doc));
        } else if (doc.length === 14) {
            // CNPJ
            frm.set_value("cpf_cnpj", erpnext_fiscal_br.formatar_cnpj(doc));
        }
    },
    
    contribuinte_icms: function(frm) {
        // Se for contribuinte, IE é obrigatória
        if (frm.doc.contribuinte_icms && frm.doc.contribuinte_icms.includes("1")) {
            frm.set_df_property("inscricao_estadual_cliente", "reqd", 1);
        } else {
            frm.set_df_property("inscricao_estadual_cliente", "reqd", 0);
        }
    }
});
