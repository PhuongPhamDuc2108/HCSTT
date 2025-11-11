// API Configuration
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

// ==================== LOAD INITIAL DATA ====================
window.addEventListener('DOMContentLoaded', function() {
    loadInitialData();
});

function loadInitialData() {
    const table = document.getElementById('ruleTable');
    const tbody = table.getElementsByTagName('tbody')[0];
    tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">Chưa có dữ liệu. Vui lòng tải lên file luật.</td></tr>';
}

// ==================== UPLOAD FILE ====================
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
            
            allRules = jsonData.map(row => ({
                id: row.ID || row.id || '',
                veTrai: row['Ve Trai'] || row.veTrai || '',
                vePhai: row['Ve Phai'] || row.vePhai || '',
                note: row.Note || row.note || ''
            }));
            
            hienThiBangLuat(allRules);
            statusDiv.innerHTML = `<div class="success">✅ Đã tải lên thành công ${allRules.length} luật!</div>`;
            
            setTimeout(() => {
                statusDiv.innerHTML = '';
            }, 3000);
            
        } catch (error) {
            console.error('Error:', error);
            statusDiv.innerHTML = '<div class="error">❌ Lỗi khi đọc file!</div>';
        }
    };
    
    reader.readAsArrayBuffer(file);
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

function searchRules() {
    const input = document.getElementById('searchBox').value.toLowerCase();
    const tbody = document.getElementById('ruleTable').getElementsByTagName('tbody')[0];
    const rows = tbody.getElementsByTagName('tr');
    
    for (let row of rows) {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(input) ? '' : 'none';
    }
}

function themLuatMoi() {
    const newId = allRules.length > 0 ? Math.max(...allRules.map(r => parseInt(r.id) || 0)) + 1 : 1;
    const newRule = {
        id: newId.toString(),
        veTrai: prompt('Nhập vế trái (premise):') || '',
        vePhai: prompt('Nhập vế phải (conclusion):') || '',
        note: prompt('Nhập ghi chú (Note):') || ''
    };
    
    if (newRule.veTrai && newRule.vePhai) {
        allRules.push(newRule);
        hienThiBangLuat(allRules);
    }
}

function editRule(btn) {
    const row = btn.parentElement.parentElement;
    const cells = row.cells;
    
    cells[1].innerHTML = `<input type="text" value="${cells[1].textContent}" style="width:100%">`;
    cells[2].innerHTML = `<input type="text" value="${cells[2].textContent}" style="width:100%">`;
    cells[3].innerHTML = `<input type="text" value="${cells[3].textContent}" style="width:100%">`;
    
    btn.textContent = '💾';
    btn.onclick = function() { saveRule(btn); };
}

function saveRule(btn) {
    const row = btn.parentElement.parentElement;
    const cells = row.cells;
    const id = cells[0].textContent;
    
    const veTrai = cells[1].querySelector('input').value;
    const vePhai = cells[2].querySelector('input').value;
    const note = cells[3].querySelector('input').value;
    
    const ruleIndex = allRules.findIndex(r => r.id === id);
    if (ruleIndex !== -1) {
        allRules[ruleIndex].veTrai = veTrai;
        allRules[ruleIndex].vePhai = vePhai;
        allRules[ruleIndex].note = note;
    }
    
    hienThiBangLuat(allRules);
}

function deleteRule(btn) {
    if (!confirm('Bạn có chắc muốn xóa luật này?')) return;
    
    const row = btn.parentElement.parentElement;
    const id = row.cells[0].textContent;
    
    allRules = allRules.filter(r => r.id !== id);
    hienThiBangLuat(allRules);
}

// ==================== FPG GENERATION ====================
async function generateFPG() {
    const container = document.getElementById('fpgContainer');
    const loading = document.getElementById('fpgLoading');
    
    if (allRules.length === 0) {
        alert('⚠️ Chưa có luật nào! Vui lòng tải file luật trước.');
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
                rules: allRules,
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
        console.error('FPG Error:', error);
        container.innerHTML = '<p class="error">❌ Không thể kết nối đến server</p>';
    } finally {
        loading.style.display = 'none';
    }
}

// ==================== RPG GENERATION ====================
async function generateRPG() {
    const container = document.getElementById('rpgContainer');
    const loading = document.getElementById('rpgLoading');
    
    if (allRules.length === 0) {
        alert('⚠️ Chưa có luật nào! Vui lòng tải file luật trước.');
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
        console.error('RPG Error:', error);
        container.innerHTML = '<p class="error">❌ Không thể kết nối đến server</p>';
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
    
    if (!giathiet.trim()) {
        alert('⚠️ Vui lòng nhập giả thiết ban đầu!');
        return;
    }
    
    if (!ketqua.trim()) {
        alert('⚠️ Vui lòng nhập kết luận cần tìm!');
        return;
    }
    
    if (allRules.length === 0) {
        alert('⚠️ Chưa có luật nào trong hệ thống!');
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
                    <p><strong>Giả thiết ban đầu (GT):</strong> {${result.initial_facts.join(', ')}}</p>
                    <p><strong>Kết luận cần tìm (KL):</strong> {${result.goals.join(', ')}}</p>
                    <p><strong>Vết suy diễn (VET):</strong> ${result.optimal_vet.map(r => 'r' + r).join(' → ')}</p>
                </div>
            `;
            
            if (result.explanation && result.explanation.length > 0) {
                html += '<h3>📝 Chi tiết các bước tính toán:</h3>';
                result.explanation.forEach(step => {
                    html += `
                        <div class="step-detail">
                            <strong>Bước ${step.step}:</strong> Áp dụng luật r${step.rule}<br>
                            <strong>Tiền đề:</strong> {${step.premise.join(', ')}}<br>
                            <strong>Kết luận:</strong> ${step.conclusion}<br>
                            ${step.note ? `<strong style="color: #3498db;">📐 Công thức:</strong> ${step.note}` : ''}
                        </div>
                    `;
                });
            }
            
            ketQua.innerHTML = html;
            
            if (result.process_table && result.process_table.length > 0) {
                displayForwardProcessTable(result.process_table);
                bangQuaTrinh.style.display = 'block';
            }
            
        } else {
            ketQua.innerHTML = `
                <div class="error-box">
                    <h3>❌ Không thể chứng minh kết luận từ giả thiết đã cho</h3>
                    <p><strong>Giả thiết:</strong> {${result.initial_facts.join(', ')}}</p>
                    <p><strong>Kết quả cần tìm:</strong> {${result.goals.join(', ')}}</p>
                </div>
            `;
        }
        
    } catch (error) {
        console.error('Forward Inference Error:', error);
        ketQua.innerHTML = `
            <div class="error-box">
                <h3>❌ Không thể kết nối đến server</h3>
                <p>Vui lòng kiểm tra server đang chạy tại <code>http://localhost:5000</code></p>
            </div>
        `;
    }
}

function displayForwardProcessTable(processTable) {
    const tbody = document.getElementById('process-table-body');
    tbody.innerHTML = '';
    
    processTable.forEach(row => {
        const tr = document.createElement('tr');
        
        if (row.rule === 'DONE') {
            tr.style.backgroundColor = '#d4edda';
            tr.style.fontWeight = 'bold';
        } else if (row.rule === 'FAIL') {
            tr.style.backgroundColor = '#f8d7da';
            tr.style.fontWeight = 'bold';
        }
        
        tr.innerHTML = `
            <td>${row.step}</td>
            <td>${row.rule || '-'}</td>
            <td>{${row.THOA.join(', ')}}</td>
            <td>{${row.TG.join(', ')}}</td>
            <td>[${row.R.join(', ')}]</td>
            <td>[${row.VET.join(', ')}]</td>
            <td style="text-align: left; font-size: 11px;">
                ${row.note ? `<strong style="color: #3498db;">📝</strong> ${row.note}` : '-'}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function resetInference() {
    document.getElementById('giathiet').value = '';
    document.getElementById('ketqua').value = '';
    document.getElementById('ketQuaSuyDienChiTiet').innerHTML = 
        'Nhập giả thiết và kết quả cần tìm, sau đó nhấn "Thực hiện suy diễn tiến"...';
    document.getElementById('bang-qua-trinh').style.display = 'none';
}

// ==================== BACKWARD INFERENCE ====================
async function suydienLui() {
    const giathiet = document.getElementById('giathiet_backward').value;
    const ketqua = document.getElementById('ketqua_backward').value;
    const ketQua = document.getElementById('ketQuaSuyDienLui');
    const bangQuaTrinh = document.getElementById('bang-qua-trinh-backward');
    const traceSection = document.getElementById('backward-trace-section');
    
    if (!giathiet.trim()) {
        alert('⚠️ Vui lòng nhập giả thiết ban đầu!');
        return;
    }
    
    if (!ketqua.trim()) {
        alert('⚠️ Vui lòng nhập kết luận cần chứng minh!');
        return;
    }
    
    if (allRules.length === 0) {
        alert('⚠️ Chưa có luật nào trong hệ thống!');
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
                    <p><strong>Giả thiết ban đầu (GT):</strong> {${result.initial_facts.join(', ')}}</p>
                    <p><strong>Kết luận cần chứng minh (KL):</strong> {${result.goals.join(', ')}}</p>
                    <p><strong>Vết đầy đủ (Backward order):</strong> ${result.full_vet.map(r => 'r' + r).join(' ← ')}</p>
                    <p><strong>Vết tối ưu (Forward order để áp dụng):</strong> ${result.optimal_vet.map(r => 'r' + r).join(' → ')}</p>
                </div>
            `;
            
            if (result.explanation && result.explanation.length > 0) {
                html += '<h3>📝 Chi tiết các bước tính toán (theo thứ tự áp dụng):</h3>';
                result.explanation.forEach(step => {
                    html += `
                        <div class="backward-step-detail">
                            <strong>Bước ${step.step}:</strong> Áp dụng luật r${step.rule}<br>
                            <strong>Tiền đề cần có:</strong> {${step.premise.join(', ')}}<br>
                            <strong>Để suy ra:</strong> ${step.conclusion}<br>
                            ${step.note ? `<strong style="color: #e74c3c;">📐 Công thức:</strong> ${step.note}` : ''}
                        </div>
                    `;
                });
            }
            
            ketQua.innerHTML = html;
            
            if (result.process_table && result.process_table.length > 0) {
                displayBackwardProcessTable(result.process_table);
                bangQuaTrinh.style.display = 'block';
            }
            
            getBackwardTrace(initialFacts, goals);
            
        } else {
            ketQua.innerHTML = `
                <div class="backward-error">
                    <h3>❌ Không thể chứng minh kết luận từ giả thiết đã cho</h3>
                    <p><strong>Giả thiết:</strong> {${result.initial_facts.join(', ')}}</p>
                    <p><strong>Kết quả cần tìm:</strong> {${result.goals.join(', ')}}</p>
                    <p><strong>Lý do:</strong> Không tìm thấy chuỗi luật nào để chứng minh từ GT đến KL</p>
                </div>
            `;
        }
        
    } catch (error) {
        console.error('Backward Inference Error:', error);
        ketQua.innerHTML = `
            <div class="backward-error">
                <h3>❌ Không thể kết nối đến server</h3>
                <p>Vui lòng kiểm tra server đang chạy tại <code>http://localhost:5000</code></p>
                <p><strong>Error:</strong> ${error.message}</p>
            </div>
        `;
    }
}

async function getBackwardTrace(initialFacts, goals) {
    try {
        const response = await fetch(`${API_URL}/backward_inference_trace`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                rules: allRules,
                initial_facts: initialFacts,
                goals: goals
            })
        });
        
        const result = await response.json();
        
        if (result.success && result.trace) {
            displayBackwardTrace(result.trace);
            document.getElementById('backward-trace-section').style.display = 'block';
        }
    } catch (error) {
        console.error('Trace Error:', error);
    }
}

function displayBackwardTrace(trace) {
    const container = document.getElementById('traceContainer');
    let html = '<div style="text-align: center; font-size: 18px; line-height: 2.5;">';
    
    trace.forEach((item, index) => {
        const setStr = item.set.length === 0 || (item.set.length === 1 && item.set[0] === '∅') 
            ? '∅' 
            : `{${item.set.join(', ')}}`;
        
        html += `<span class="trace-step">${setStr}</span>`;
        
        if (item.rule) {
            html += `<span class="trace-rule">${item.rule}</span>`;
        }
        
        if (index < trace.length - 1) {
            html += `<span class="trace-arrow">←</span>`;
        }
    });
    
    html += '</div>';
    
    // Add note explanation
    html += '<div style="margin-top: 20px; padding: 15px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 5px;">';
    html += '<strong>💡 Giải thích Trace:</strong><br>';
    html += 'Đọc từ trái sang phải: Bắt đầu từ KL, thay thế dần bằng tiền đề của các luật cho đến khi tất cả đều có trong GT.<br>';
    html += 'Mũi tên ← biểu thị quá trình backward (tìm ngược).';
    html += '</div>';
    
    container.innerHTML = html;
}

function displayBackwardProcessTable(processTable) {
    const tbody = document.getElementById('process-table-body-backward');
    tbody.innerHTML = '';
    
    processTable.forEach(row => {
        const tr = document.createElement('tr');
        
        if (row.rule === 'DONE') {
            tr.style.backgroundColor = '#d4edda';
            tr.style.fontWeight = 'bold';
            tr.style.color = '#155724';
        } else if (row.rule === 'FAIL') {
            tr.style.backgroundColor = '#f8d7da';
            tr.style.fontWeight = 'bold';
            tr.style.color = '#721c24';
        }
        
        tr.innerHTML = `
            <td>${row.step}</td>
            <td>${row.rule || '-'}</td>
            <td>{${row.current_goals.join(', ')}}</td>
            <td>{${row.GT.join(', ')}}</td>
            <td>[${row.VET.join(', ')}]</td>
            <td style="text-align: left; font-size: 11px;">
                <strong>Giải thích:</strong> ${row.explanation}<br>
                ${row.note ? `<strong style="color: #e74c3c;">📝 Công thức:</strong> ${row.note}` : ''}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function resetBackwardInference() {
    document.getElementById('giathiet_backward').value = '';
    document.getElementById('ketqua_backward').value = '';
    document.getElementById('ketQuaSuyDienLui').innerHTML = 
        'Nhập giả thiết và kết luận cần chứng minh, sau đó nhấn "Thực hiện suy diễn lùi"...';
    document.getElementById('bang-qua-trinh-backward').style.display = 'none';
    document.getElementById('backward-trace-section').style.display = 'none';
}
