// app.js
const API_URL = 'http://localhost:5000';
let allRules = [];
let savedInitialFacts = [];
let savedGoals = [];

// ==================== MENU NAVIGATION ====================
const menuItems = document.querySelectorAll('.menu-item');
const contentSections = document.querySelectorAll('.content-section');

menuItems.forEach(item => {
    item.addEventListener('click', function() {
        menuItems.forEach(mi => mi.classList.remove('active'));
        contentSections.forEach(cs => cs.classList.remove('active'));
        
        this.classList.add('active');
        const targetId = this.getAttribute('data-target');
        document.getElementById(targetId).classList.add('active');
    });
});

// ==================== LOAD DATA FROM SERVER ====================
window.addEventListener('DOMContentLoaded', function() {
    fetchRulesFromServer();
});

async function fetchRulesFromServer() {
    try {
        const response = await fetch(`${API_URL}/rules`);
        const rules = await response.json();
        allRules = rules;
        if (allRules.length > 0) {
            hienThiBangLuat(allRules);
        } else {
            const tbody = document.getElementById('ruleTable').getElementsByTagName('tbody')[0];
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">Chưa có dữ liệu. Vui lòng tải lên file luật hoặc thêm mới.</td></tr>';
        }
    } catch (error) {
        console.error('Error loading rules:', error);
    }
}

// ==================== UPLOAD FILE & SAVE TO SERVER ====================
function taiLenTapLuat(event) {
    const file = event.target.files[0];
    const statusDiv = document.getElementById('uploadStatus');
    
    if (!file) return;
    
    statusDiv.innerHTML = '<div class="loading show">⏳ Đang xử lý file...</div>';
    
    const reader = new FileReader();
    
    reader.onload = function(e) {
        try {
            const data = new Uint8Array(e.target.result);
            const workbook = XLSX.read(data, {type: 'array'});
            const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
            const jsonData = XLSX.utils.sheet_to_json(firstSheet);
            
            if (jsonData.length === 0) {
                statusDiv.innerHTML = '<div class="error">❌ File không có dữ liệu!</div>';
                return;
            }
            
            // Parse data
            const parsedRules = jsonData.map(row => ({
                id: (row.ID || row.id || '').toString(),
                veTrai: (row['Ve Trai'] || row.veTrai || '').toString(),
                vePhai: (row['Ve Phai'] || row.vePhai || '').toString(),
                note: (row.Note || row.note || '').toString()
            }));
            
            // Gửi lên server để lưu
            saveRulesToServer(parsedRules, statusDiv);
            
        } catch (error) {
            console.error('Error:', error);
            statusDiv.innerHTML = '<div class="error">❌ Lỗi khi đọc file!</div>';
        }
    };
    
    reader.readAsArrayBuffer(file);
}

async function saveRulesToServer(rules, statusDiv) {
    try {
        const response = await fetch(`${API_URL}/rules/upload`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ rules: rules })
        });
        
        const result = await response.json();
        
        if (result.success) {
            allRules = rules;
            hienThiBangLuat(allRules);
            statusDiv.innerHTML = `<div class="success">✅ ${result.message}</div>`;
            setTimeout(() => { statusDiv.innerHTML = ''; }, 3000);
        } else {
            statusDiv.innerHTML = `<div class="error">❌ Lỗi server: ${result.error}</div>`;
        }
    } catch (error) {
        statusDiv.innerHTML = '<div class="error">❌ Không thể kết nối đến server để lưu!</div>';
    }
}

function hienThiBangLuat(rules) {
    const tbody = document.getElementById('ruleTable').getElementsByTagName('tbody')[0];
    tbody.innerHTML = '';
    
    rules.forEach(rule => {
        const row = tbody.insertRow();
        row.innerHTML = `
            <td>${rule.id}</td>
            <td>${rule.veTrai}</td>
            <td>${rule.vePhai}</td>
            <td style="font-size: 11px; color: #555;">${rule.note || '-'}</td>
            <td>
                <button class="action-btn edit-btn" onclick="editRule(this)">✏️</button>
                <button class="action-btn delete-btn" onclick="deleteRule(this)">🗑️</button>
            </td>
        `;
    });
}

// ==================== CRUD ACTIONS (SYNC WITH SERVER) ====================

function searchRules() {
    const input = document.getElementById('searchBox').value.toLowerCase();
    const tbody = document.getElementById('ruleTable').getElementsByTagName('tbody')[0];
    const rows = tbody.getElementsByTagName('tr');
    
    for (let row of rows) {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(input) ? '' : 'none';
    }
}

async function themLuatMoi() {
    // Tìm ID lớn nhất hiện tại để gợi ý (Server sẽ xử lý chính, nhưng client làm cho đẹp)
    const maxId = allRules.length > 0 
        ? Math.max(...allRules.map(r => parseInt(r.id) || 0)) 
        : 0;
        
    const newId = (maxId + 1).toString();
    
    const veTrai = prompt('Nhập vế trái (premise):');
    if (veTrai === null) return; 
    
    const vePhai = prompt('Nhập vế phải (conclusion):');
    if (vePhai === null) return;

    const note = prompt('Nhập ghi chú (Note):') || '';

    if (veTrai && vePhai) {
        const newRule = { id: newId, veTrai, vePhai, note };
        
        try {
            const response = await fetch(`${API_URL}/rules/add`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ rule: newRule })
            });
            
            const result = await response.json();
            if (result.success) {
                allRules = result.rules;
                hienThiBangLuat(allRules);
                alert('✅ Đã thêm luật mới và lưu vào server!');
            } else {
                alert('❌ Lỗi: ' + result.error);
            }
        } catch (error) {
            alert('❌ Lỗi kết nối server');
        }
    }
}

function editRule(btn) {
    const row = btn.parentElement.parentElement;
    const cells = row.cells;
    
    cells[1].innerHTML = `<input type="text" value="${cells[1].textContent}" style="width:100%">`;
    cells[2].innerHTML = `<input type="text" value="${cells[2].textContent}" style="width:100%">`;
    cells[3].innerHTML = `<input type="text" value="${cells[3].textContent}" style="width:100%">`;
    
    btn.textContent = '💾';
    btn.onclick = function() { saveRuleEdit(btn); }; // Đổi tên hàm để tránh nhầm lẫn
}

async function saveRuleEdit(btn) {
    const row = btn.parentElement.parentElement;
    const cells = row.cells;
    const id = cells[0].textContent;
    
    const veTrai = cells[1].querySelector('input').value;
    const vePhai = cells[2].querySelector('input').value;
    const note = cells[3].querySelector('input').value;
    
    const updatedRule = { id, veTrai, vePhai, note };
    
    try {
        const response = await fetch(`${API_URL}/rules/update`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ rule: updatedRule })
        });
        
        const result = await response.json();
        if (result.success) {
            allRules = result.rules;
            hienThiBangLuat(allRules);
        } else {
            alert('❌ Lỗi: ' + result.error);
            fetchRulesFromServer(); // Reload lại dữ liệu cũ nếu lỗi
        }
    } catch (error) {
        alert('❌ Lỗi kết nối server');
    }
}

async function deleteRule(btn) {
    if (!confirm('Bạn có chắc muốn xóa luật này vĩnh viễn?')) return;
    
    const row = btn.parentElement.parentElement;
    const id = row.cells[0].textContent;
    
    try {
        const response = await fetch(`${API_URL}/rules/delete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: id })
        });
        
        const result = await response.json();
        if (result.success) {
            allRules = result.rules;
            hienThiBangLuat(allRules);
        } else {
            alert('❌ Lỗi: ' + result.error);
        }
    } catch (error) {
        alert('❌ Lỗi kết nối server');
    }
}

// ==================== GENERATE FPG ====================
async function generateFPG() {
    const container = document.getElementById('fpgContainer');
    const loading = document.getElementById('fpgLoading');
    
    if (allRules.length === 0) {
        alert('⚠️ Chưa có luật nào!');
        return;
    }
    
    if (savedInitialFacts.length === 0 || savedGoals.length === 0) {
        alert('⚠️ Vui lòng chạy suy diễn trước để có GT và KL!');
        return;
    }
    
    loading.style.display = 'block';
    container.innerHTML = '';
    
    try {
        const response = await fetch(`${API_URL}/generate_fpg`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                rules: allRules, // Gửi rules hiện tại (hoặc để null server tự load)
                initial_facts: savedInitialFacts,
                target_goals: savedGoals,
                layout_method: 'kamada_kawai'
            })
        });
        
        const result = await response.json();
        if (result.success) {
            container.innerHTML = `<img src="data:image/png;base64,${result.image}" alt="FPG Graph" style="max-width: 100%;">`;
        } else {
            container.innerHTML = `<p class="error">❌ ${result.error}</p>`;
        }
    } catch (error) {
        container.innerHTML = '<p class="error">❌ Lỗi kết nối</p>';
    } finally {
        loading.style.display = 'none';
    }
}

// ==================== GENERATE RPG ====================
async function generateRPG() {
    const container = document.getElementById('rpgContainer');
    const loading = document.getElementById('rpgLoading');
    
    if (allRules.length === 0) {
        alert('⚠️ Chưa có luật nào!');
        return;
    }
    
    loading.style.display = 'block';
    container.innerHTML = '';
    
    try {
        const response = await fetch(`${API_URL}/generate_rpg`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                rules: allRules,
                initial_facts: savedInitialFacts,
                target_goals: savedGoals
            })
        });
        
        const result = await response.json();
        if (result.success) {
            container.innerHTML = `<img src="data:image/png;base64,${result.image}" alt="RPG Graph" style="max-width: 100%;">`;
        } else {
            container.innerHTML = `<p class="error">❌ ${result.error}</p>`;
        }
    } catch (error) {
        container.innerHTML = '<p class="error">❌ Lỗi kết nối</p>';
    } finally {
        loading.style.display = 'none';
    }
}

// ==================== FORWARD INFERENCE ====================
async function suydienChiTiet() {
    const giathiet = document.getElementById('giathiet').value;
    const ketqua = document.getElementById('ketqua').value;
    const ketQua = document.getElementById('ketQuaSuyDienChiTiet');
    const bangQuaTrinh = document.getElementById('bang-qua-trinh');
    
    if (!giathiet.trim() || !ketqua.trim()) {
        alert('⚠️ Vui lòng nhập giả thiết và kết luận!');
        return;
    }
    
    const initialFacts = giathiet.split(',').map(f => f.trim()).filter(f => f);
    const goals = ketqua.split(',').map(g => g.trim()).filter(g => g);
    savedInitialFacts = initialFacts;
    savedGoals = goals;
    
    ketQua.innerHTML = '<div class="loading show">⏳ Đang thực hiện suy diễn tiến...</div>';
    bangQuaTrinh.style.display = 'none';
    
    try {
        const response = await fetch(`${API_URL}/forward_inference_advanced`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                rules: allRules,
                initial_facts: initialFacts,
                goals: goals
            })
        });
        
        const result = await response.json();
        if (result.success) {
            let html = `
                <div class="success-box">
                    <h3>✅ Suy diễn tiến thành công!</h3>
                    <p><strong>Vết suy diễn:</strong> ${result.optimal_vet.map(r => 'r' + r).join(' → ')}</p>
                </div>`;
            
            if (result.explanation) {
                html += '<h3>📝 Chi tiết các bước:</h3>';
                result.explanation.forEach(step => {
                    html += `<div class="step-detail">
                            <strong>Bước ${step.step} (r${step.rule}):</strong> {${step.premise.join(', ')}} → ${step.conclusion}
                        </div>`;
                });
            }
            ketQua.innerHTML = html;
            if (result.process_table) {
                displayForwardProcessTable(result.process_table);
                bangQuaTrinh.style.display = 'block';
            }
        } else {
            ketQua.innerHTML = `<div class="error-box"><h3>❌ Thất bại</h3><p>${result.conclusion}</p></div>`;
        }
    } catch (error) {
        ketQua.innerHTML = '<div class="error-box">❌ Lỗi server</div>';
    }
}

function displayForwardProcessTable(processTable) {
    const tbody = document.getElementById('process-table-body');
    tbody.innerHTML = '';
    processTable.forEach(row => {
        const tr = document.createElement('tr');
        if (row.rule === 'DONE') tr.style.backgroundColor = '#d4edda';
        if (row.rule === 'FAIL') tr.style.backgroundColor = '#f8d7da';
        
        tr.innerHTML = `
            <td>${row.step}</td>
            <td>${row.rule}</td>
            <td>{${row.THOA.join(', ')}}</td>
            <td>{${row.TG.join(', ')}}</td>
            <td>[${row.R.join(', ')}]</td>
            <td>[${row.VET.join(', ')}]</td>
            <td style="text-align: left; font-size: 11px;">${row.note || '-'}</td>
        `;
        tbody.appendChild(tr);
    });
}

function resetInference() {
    document.getElementById('giathiet').value = '';
    document.getElementById('ketqua').value = '';
    document.getElementById('ketQuaSuyDienChiTiet').innerHTML = '...';
    document.getElementById('bang-qua-trinh').style.display = 'none';
}

// ==================== BACKWARD INFERENCE ====================
async function suydienLui() {
    const giathiet = document.getElementById('giathiet_backward').value;
    const ketqua = document.getElementById('ketqua_backward').value;
    const ketQua = document.getElementById('ketQuaSuyDienLui');
    const bangQuaTrinh = document.getElementById('bang-qua-trinh-backward');
    const traceSection = document.getElementById('backward-trace-section');
    
    if (!giathiet.trim() || !ketqua.trim()) {
        alert('⚠️ Vui lòng nhập giả thiết và kết luận!');
        return;
    }
    
    const initialFacts = giathiet.split(',').map(f => f.trim()).filter(f => f);
    const goals = ketqua.split(',').map(g => g.trim()).filter(g => g);
    savedInitialFacts = initialFacts;
    savedGoals = goals;
    
    ketQua.innerHTML = '<div class="loading show">⏳ Đang thực hiện suy diễn lùi...</div>';
    bangQuaTrinh.style.display = 'none';
    traceSection.style.display = 'none';
    
    try {
        const response = await fetch(`${API_URL}/backward_inference_advanced`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                rules: allRules,
                initial_facts: initialFacts,
                goals: goals
            })
        });
        
        const result = await response.json();
        if (result.success) {
            let html = `
                <div class="backward-success">
                    <h3>✅ Suy diễn lùi thành công!</h3>
                    <p><strong>Vết tối ưu:</strong> ${result.optimal_vet.map(r => 'r' + r).join(' → ')}</p>
                </div>`;
            
            if (result.explanation) {
                html += '<h3>📝 Chi tiết:</h3>';
                result.explanation.forEach(step => {
                    html += `<div class="backward-step-detail">
                            <strong>Bước ${step.step} (r${step.rule}):</strong> Cần {${step.premise.join(', ')}} để có ${step.conclusion}
                        </div>`;
                });
            }
            ketQua.innerHTML = html;
            if (result.process_table) {
                displayBackwardProcessTable(result.process_table);
                bangQuaTrinh.style.display = 'block';
            }
            getBackwardTrace(initialFacts, goals);
        } else {
            ketQua.innerHTML = `<div class="backward-error"><h3>❌ Thất bại</h3><p>${result.conclusion}</p></div>`;
        }
    } catch (error) {
        ketQua.innerHTML = '<div class="backward-error">❌ Lỗi server</div>';
    }
}

async function getBackwardTrace(initialFacts, goals) {
    try {
        const response = await fetch(`${API_URL}/backward_inference_trace`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ rules: allRules, initial_facts: initialFacts, goals: goals })
        });
        const result = await response.json();
        if (result.success && result.trace) {
            displayBackwardTrace(result.trace);
            document.getElementById('backward-trace-section').style.display = 'block';
        }
    } catch (e) { console.error(e); }
}

function displayBackwardTrace(trace) {
    const container = document.getElementById('traceContainer');
    let html = '<div style="text-align: center; font-size: 18px; line-height: 2.5;">';
    trace.forEach((item, index) => {
        const setStr = item.set.length === 0 || (item.set.length === 1 && item.set[0] === '∅') ? '∅' : `{${item.set.join(', ')}}`;
        html += `<span class="trace-step">${setStr}</span>`;
        if (item.rule) html += `<span class="trace-rule">${item.rule}</span>`;
        if (index < trace.length - 1) html += `<span class="trace-arrow">←</span>`;
    });
    html += '</div>';
    container.innerHTML = html;
}

function displayBackwardProcessTable(processTable) {
    const tbody = document.getElementById('process-table-body-backward');
    tbody.innerHTML = '';
    processTable.forEach(row => {
        const tr = document.createElement('tr');
        if (row.rule === 'DONE') tr.style.backgroundColor = '#d4edda';
        if (row.rule === 'FAIL') tr.style.backgroundColor = '#f8d7da';
        tr.innerHTML = `
            <td>${row.step}</td>
            <td>${row.rule}</td>
            <td>{${row.current_goals.join(', ')}}</td>
            <td>{${row.GT.join(', ')}}</td>
            <td>[${row.VET.join(', ')}]</td>
            <td style="text-align: left;">${row.explanation}</td>
        `;
        tbody.appendChild(tr);
    });
}

function resetBackwardInference() {
    document.getElementById('giathiet_backward').value = '';
    document.getElementById('ketqua_backward').value = '';
    document.getElementById('ketQuaSuyDienLui').innerHTML = '...';
    document.getElementById('bang-qua-trinh-backward').style.display = 'none';
    document.getElementById('backward-trace-section').style.display = 'none';
}